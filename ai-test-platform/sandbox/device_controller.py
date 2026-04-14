#!/usr/bin/env python3
"""
设备控制器
管理 Docker 沙箱中的设备连接（用于远程设备调试）
"""
import json
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DeviceConnection:
    """设备连接信息"""
    device_id: str
    platform: str  # android/ios
    host: str
    port: int
    status: str = "available"  # available/busy/error
    last_used: Optional[float] = None


class DeviceController:
    """设备控制器"""

    def __init__(self):
        self.connections: Dict[str, DeviceConnection] = {}
        self._adb_path = "adb"
        self._xcrun_path = "xcrun"

    def add_android_device(self, device_id: str, host: str, port: int = 5555) -> bool:
        """添加 Android 设备连接"""
        conn = DeviceConnection(
            device_id=device_id,
            platform="android",
            host=host,
            port=port,
        )
        self.connections[device_id] = conn
        return self._verify_android_connection(conn)

    def add_ios_device(self, device_id: str, host: str = "localhost") -> bool:
        """添加 iOS 设备连接"""
        conn = DeviceConnection(
            device_id=device_id,
            platform="ios",
            host=host,
            port=8100,  # 默认 WDA 端口
        )
        self.connections[device_id] = conn
        return self._verify_ios_connection(conn)

    def _verify_android_connection(self, conn: DeviceConnection) -> bool:
        """验证 Android 设备连接"""
        try:
            result = subprocess.run(
                [self._adb_path, "-s", f"{conn.host}:{conn.port}", "get-state"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "device" in result.stdout.lower()
        except Exception:
            return False

    def _verify_ios_connection(self, conn: DeviceConnection) -> bool:
        """验证 iOS 设备连接"""
        # iOS 设备验证比较复杂，这里简化处理
        return True

    def remove_device(self, device_id: str) -> bool:
        """移除设备"""
        if device_id in self.connections:
            del self.connections[device_id]
            return True
        return False

    def get_device(self, device_id: str) -> Optional[DeviceConnection]:
        """获取设备"""
        return self.connections.get(device_id)

    def list_devices(self, platform: Optional[str] = None) -> List[DeviceConnection]:
        """列出设备"""
        if platform:
            return [d for d in self.connections.values() if d.platform == platform]
        return list(self.connections.values())

    def reserve_device(self, device_id: str) -> bool:
        """预留设备"""
        conn = self.connections.get(device_id)
        if conn and conn.status == "available":
            conn.status = "busy"
            conn.last_used = time.time()
            return True
        return False

    def release_device(self, device_id: str) -> bool:
        """释放设备"""
        conn = self.connections.get(device_id)
        if conn and conn.status == "busy":
            conn.status = "available"
            return True
        return False

    def execute_android_command(self, device_id: str, command: List[str]) -> Dict[str, Any]:
        """执行 ADB 命令"""
        conn = self.connections.get(device_id)
        if not conn or conn.platform != "android":
            return {"success": False, "error": "Device not found or not Android"}

        cmd = [self._adb_path, "-s", f"{conn.host}:{conn.port}"] + command

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def screenshot_android(self, device_id: str, output_path: str) -> bool:
        """Android 设备截图"""
        result = self.execute_android_command(
            device_id,
            ["exec-out", "screenshot"]
        )
        if result["success"]:
            try:
                import base64
                data = result["stdout"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(data))
                return True
            except Exception:
                return False
        return False

    def forward_port(self, device_id: str, local: int, remote: int) -> Optional[int]:
        """端口转发"""
        result = self.execute_android_command(
            device_id,
            ["forward", f"tcp:{local}", f"tcp:{remote}"]
        )
        if result["success"]:
            return local
        return None

    def reverse_port(self, device_id: str, remote: int, local: int) -> Optional[int]:
        """反向端口转发"""
        result = self.execute_android_command(
            device_id,
            ["reverse", f"tcp:{remote}", f"tcp:{local}"]
        )
        if result["success"]:
            return remote
        return None

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """获取设备信息"""
        conn = self.connections.get(device_id)
        if not conn:
            return {}

        info = {
            "device_id": conn.device_id,
            "platform": conn.platform,
            "host": conn.host,
            "port": conn.port,
            "status": conn.status,
        }

        if conn.platform == "android":
            result = self.execute_android_command(device_id, ["shell", "getprop"])
            if result["success"]:
                props = {}
                for line in result["stdout"].split("\n"):
                    if ":" in line:
                        parts = line[1:-1].split("]: [")
                        if len(parts) == 2:
                            props[parts[0]] = parts[1]
                info["properties"] = props
                info["model"] = props.get("ro.product.model", "Unknown")
                info["version"] = props.get("ro.build.version.release", "Unknown")

        return info

    def cleanup_idle_devices(self, idle_timeout: int = 3600) -> int:
        """清理空闲设备"""
        current_time = time.time()
        cleaned = 0

        for conn in self.connections.values():
            if conn.status == "busy" and conn.last_used:
                if current_time - conn.last_used > idle_timeout:
                    self.release_device(conn.device_id)
                    cleaned += 1

        return cleaned


# 全局单例
_controller: Optional[DeviceController] = None


def get_device_controller() -> DeviceController:
    """获取设备控制器单例"""
    global _controller
    if _controller is None:
        _controller = DeviceController()
    return _controller


if __name__ == "__main__":
    # 简单测试
    controller = DeviceController()

    # 添加设备
    print("Adding Android device...")
    success = controller.add_android_device("test-device", "192.168.1.100", 5555)
    print(f"Device added: {success}")

    # 列出设备
    devices = controller.list_devices()
    print(f"Devices: {len(devices)}")

    # 获取设备信息
    info = controller.get_device_info("test-device")
    print(f"Device info: {json.dumps(info, indent=2)}")
