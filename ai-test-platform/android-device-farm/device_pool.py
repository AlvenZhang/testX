"""Android设备池管理 - 管理设备的分配和回收"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """设备信息"""
    serial: str
    name: str
    version: str
    status: str = "offline"  # online/offline/busy/maintaining
    current_run_id: Optional[str] = None
    appium_port: Optional[int] = None
    capabilities: Dict = field(default_factory=dict)
    last_used: Optional[datetime] = None

    def is_available(self) -> bool:
        """检查设备是否可用"""
        return self.status == "online" and self.current_run_id is None


class DevicePool:
    """Android设备池"""

    def __init__(self):
        self._available: List[DeviceInfo] = []
        self._busy: Dict[str, DeviceInfo] = {}
        self._lock = asyncio.Lock()
        self._listeners: List[asyncio.Queue] = []

    async def add_device(self, device: DeviceInfo) -> None:
        """
        添加设备到池中

        Args:
            device: 设备信息
        """
        async with self._lock:
            # 检查设备是否已存在
            existing = next((d for d in self._available if d.serial == device.serial), None)
            if existing:
                logger.warning(f"Device {device.serial} already exists in pool")
                return

            self._available.append(device)
            logger.info(f"Device {device.serial} added to pool, status: {device.status}")
            await self._notify_listeners("device_added", device)

    async def remove_device(self, serial: str) -> bool:
        """
        从池中移除设备

        Args:
            serial: 设备序列号

        Returns:
            是否成功移除
        """
        async with self._lock:
            device = next((d for d in self._available if d.serial == serial), None)
            if device is None:
                return False

            if device.status == "busy":
                logger.warning(f"Cannot remove busy device {serial}")
                return False

            self._available.remove(device)
            logger.info(f"Device {serial} removed from pool")
            await self._notify_listeners("device_removed", device)
            return True

    async def acquire_device(self, serial: Optional[str] = None, run_id: Optional[str] = None) -> Optional[DeviceInfo]:
        """
        获取可用设备

        Args:
            serial: 指定设备序列号，为None则获取任意可用设备
            run_id: 执行ID，用于标记设备被占用

        Returns:
            可用设备信息，None表示无可用设备
        """
        async with self._lock:
            if serial:
                # 获取指定设备
                device = next((d for d in self._available if d.serial == serial), None)
                if device and device.is_available():
                    device.status = "busy"
                    device.current_run_id = run_id
                    device.last_used = datetime.utcnow()
                    self._busy[serial] = device
                    self._available.remove(device)
                    logger.info(f"Device {serial} acquired for run {run_id}")
                    await self._notify_listeners("device_acquired", device)
                    return device
                return None
            else:
                # 获取任意可用设备
                device = next((d for d in self._available if d.is_available()), None)
                if device:
                    device.status = "busy"
                    device.current_run_id = run_id
                    device.last_used = datetime.utcnow()
                    self._busy[serial] = device
                    self._available.remove(device)
                    logger.info(f"Device {device.serial} acquired for run {run_id}")
                    await self._notify_listeners("device_acquired", device)
                    return device
                return None

    async def release_device(self, serial: str) -> bool:
        """
        释放设备回池中

        Args:
            serial: 设备序列号

        Returns:
            是否成功释放
        """
        async with self._lock:
            device = self._busy.get(serial)
            if device is None:
                logger.warning(f"Device {serial} is not in busy pool")
                return False

            device.status = "online"
            device.current_run_id = None
            self._busy.pop(serial)
            self._available.append(device)
            logger.info(f"Device {serial} released back to pool")
            await self._notify_listeners("device_released", device)
            return True

    async def update_device_status(self, serial: str, status: str) -> bool:
        """
        更新设备状态

        Args:
            serial: 设备序列号
            status: 新状态

        Returns:
            是否成功更新
        """
        async with self._lock:
            device = next((d for d in self._available if d.serial == serial), None)
            if device is None:
                device = self._busy.get(serial)

            if device is None:
                return False

            device.status = status
            logger.info(f"Device {serial} status updated to {status}")
            await self._notify_listeners("device_status_changed", device)
            return True

    def get_available_devices(self) -> List[DeviceInfo]:
        """获取所有可用设备"""
        return [d for d in self._available if d.is_available()]

    def get_all_devices(self) -> List[DeviceInfo]:
        """获取所有设备"""
        return self._available + list(self._busy.values())

    def get_busy_devices(self) -> List[DeviceInfo]:
        """获取所有忙碌设备"""
        return list(self._busy.values())

    async def subscribe(self, queue: asyncio.Queue) -> None:
        """订阅设备池事件"""
        self._listeners.append(queue)

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        """取消订阅"""
        if queue in self._listeners:
            self._listeners.remove(queue)

    async def _notify_listeners(self, event: str, device: DeviceInfo) -> None:
        """通知所有监听器"""
        for queue in self._listeners:
            try:
                await queue.put({"event": event, "device": device})
            except Exception as e:
                logger.error(f"Failed to notify listener: {e}")

    async def cleanup_stale_devices(self, timeout_seconds: int = 3600) -> int:
        """
        清理超时的设备

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            清理的设备数量
        """
        async with self._lock:
            now = datetime.utcnow()
            stale_devices = []

            for serial, device in self._busy.items():
                if device.last_used and (now - device.last_used).total_seconds() > timeout_seconds:
                    stale_devices.append(serial)

            for serial in stale_devices:
                device = self._busy.pop(serial)
                device.status = "maintaining"
                device.current_run_id = None
                self._available.append(device)
                logger.warning(f"Stale device {serial} returned to pool for maintenance")

            return len(stale_devices)


# 全局设备池实例
_global_device_pool: Optional[DevicePool] = None


def get_device_pool() -> DevicePool:
    """获取全局设备池实例"""
    global _global_device_pool
    if _global_device_pool is None:
        _global_device_pool = DevicePool()
    return _global_device_pool
