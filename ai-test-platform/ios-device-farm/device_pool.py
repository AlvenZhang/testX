"""iOS设备池管理 - 管理iOS设备的分配和回收"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class iOSDeviceInfo:
    """iOS设备信息"""
    udid: str
    name: str
    version: str
    is_simulator: bool
    status: str = "offline"  # online/offline/busy/maintaining
    current_run_id: Optional[str] = None
    wda_port: Optional[int] = None
    capabilities: Dict = field(default_factory=dict)
    last_used: Optional[datetime] = None

    def is_available(self) -> bool:
        """检查设备是否可用"""
        return self.status == "online" and self.current_run_id is None


class iOSDevicePool:
    """iOS设备池"""

    def __init__(self):
        self._available: List[iOSDeviceInfo] = []
        self._busy: Dict[str, iOSDeviceInfo] = {}
        self._lock = asyncio.Lock()
        self._listeners: List[asyncio.Queue] = []

    async def add_device(self, device: iOSDeviceInfo) -> None:
        """
        添加设备到池中

        Args:
            device: 设备信息
        """
        async with self._lock:
            existing = next((d for d in self._available if d.udid == device.udid), None)
            if existing:
                logger.warning(f"Device {device.udid} already exists in pool")
                return

            self._available.append(device)
            logger.info(f"iOS Device {device.udid} ({device.name}) added to pool, status: {device.status}")
            await self._notify_listeners("device_added", device)

    async def remove_device(self, udid: str) -> bool:
        """
        从池中移除设备

        Args:
            udid: 设备UDID

        Returns:
            是否成功移除
        """
        async with self._lock:
            device = next((d for d in self._available if d.udid == udid), None)
            if device is None:
                return False

            if device.status == "busy":
                logger.warning(f"Cannot remove busy device {udid}")
                return False

            self._available.remove(device)
            logger.info(f"iOS Device {udid} removed from pool")
            await self._notify_listeners("device_removed", device)
            return True

    async def acquire_device(self, udid: Optional[str] = None, run_id: Optional[str] = None) -> Optional[iOSDeviceInfo]:
        """
        获取可用设备

        Args:
            udid: 指定设备UDID，为None则获取任意可用设备
            run_id: 执行ID

        Returns:
            可用设备信息
        """
        async with self._lock:
            if udid:
                device = next((d for d in self._available if d.udid == udid), None)
                if device and device.is_available():
                    device.status = "busy"
                    device.current_run_id = run_id
                    device.last_used = datetime.utcnow()
                    self._busy[udid] = device
                    self._available.remove(device)
                    logger.info(f"iOS Device {udid} acquired for run {run_id}")
                    await self._notify_listeners("device_acquired", device)
                    return device
                return None
            else:
                device = next((d for d in self._available if d.is_available()), None)
                if device:
                    device.status = "busy"
                    device.current_run_id = run_id
                    device.last_used = datetime.utcnow()
                    self._busy[udid] = device
                    self._available.remove(device)
                    logger.info(f"iOS Device {device.udid} acquired for run {run_id}")
                    await self._notify_listeners("device_acquired", device)
                    return device
                return None

    async def release_device(self, udid: str) -> bool:
        """
        释放设备回池中

        Args:
            udid: 设备UDID

        Returns:
            是否成功释放
        """
        async with self._lock:
            device = self._busy.get(udid)
            if device is None:
                logger.warning(f"Device {udid} is not in busy pool")
                return False

            device.status = "online"
            device.current_run_id = None
            self._busy.pop(udid)
            self._available.append(device)
            logger.info(f"iOS Device {udid} released back to pool")
            await self._notify_listeners("device_released", device)
            return True

    async def update_device_status(self, udid: str, status: str) -> bool:
        """
        更新设备状态

        Args:
            udid: 设备UDID
            status: 新状态

        Returns:
            是否成功更新
        """
        async with self._lock:
            device = next((d for d in self._available if d.udid == udid), None)
            if device is None:
                device = self._busy.get(udid)

            if device is None:
                return False

            device.status = status
            logger.info(f"iOS Device {udid} status updated to {status}")
            await self._notify_listeners("device_status_changed", device)
            return True

    def get_available_devices(self) -> List[iOSDeviceInfo]:
        """获取所有可用设备"""
        return [d for d in self._available if d.is_available()]

    def get_all_devices(self) -> List[iOSDeviceInfo]:
        """获取所有设备"""
        return self._available + list(self._busy.values())

    def get_busy_devices(self) -> List[iOSDeviceInfo]:
        """获取所有忙碌设备"""
        return list(self._busy.values())

    async def subscribe(self, queue: asyncio.Queue) -> None:
        """订阅设备池事件"""
        self._listeners.append(queue)

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        """取消订阅"""
        if queue in self._listeners:
            self._listeners.remove(queue)

    async def _notify_listeners(self, event: str, device: iOSDeviceInfo) -> None:
        """通知所有监听器"""
        for queue in self._listeners:
            try:
                await queue.put({"event": event, "device": device})
            except Exception as e:
                logger.error(f"Failed to notify listener: {e}")

    async def cleanup_stale_devices(self, timeout_seconds: int = 3600) -> int:
        """清理超时的设备"""
        async with self._lock:
            now = datetime.utcnow()
            stale_devices = []

            for udid, device in self._busy.items():
                if device.last_used and (now - device.last_used).total_seconds() > timeout_seconds:
                    stale_devices.append(udid)

            for udid in stale_devices:
                device = self._busy.pop(udid)
                device.status = "maintaining"
                device.current_run_id = None
                self._available.append(device)
                logger.warning(f"Stale iOS device {udid} returned to pool for maintenance")

            return len(stale_devices)


# 全局设备池实例
_global_ios_device_pool: Optional[iOSDevicePool] = None


def get_ios_device_pool() -> iOSDevicePool:
    """获取全局iOS设备池实例"""
    global _global_ios_device_pool
    if _global_ios_device_pool is None:
        _global_ios_device_pool = iOSDevicePool()
    return _global_ios_device_pool