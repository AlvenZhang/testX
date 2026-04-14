"""设备管理服务 - Android/iOS 设备"""
import subprocess
import re
from typing import List, Dict, Optional


class DeviceService:
    """设备管理服务"""

    async def discover_android_devices(self) -> List[Dict]:
        """发现 Android 设备 (通过 ADB)"""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            devices = []
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        serial, status = parts[0].strip(), parts[1].strip()
                        # Get device info
                        info = await self._get_android_device_info(serial)
                        devices.append({
                            "serial": serial,
                            "status": status,
                            "platform": "android",
                            **info
                        })
            return devices
        except Exception as e:
            return []

    async def _get_android_device_info(self, serial: str) -> Dict:
        """获取 Android 设备详细信息"""
        info = {}
        try:
            # Get model
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.model"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["model"] = result.stdout.strip()

            # Get manufacturer
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.manufacturer"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["manufacturer"] = result.stdout.strip()

            # Get OS version
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.build.version.release"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["os_version"] = result.stdout.strip()
        except Exception:
            pass
        return info

    async def discover_ios_devices(self) -> List[Dict]:
        """发现 iOS 设备 (通过 XCRun)"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                capture_output=True,
                text=True,
                timeout=15
            )
            devices = []
            # Parse output
            lines = result.stdout.split("\n")
            current_device = None
            for line in lines:
                # Match device patterns like "iPhone 15 Pro (ABC12345-1234-1234-1234-123456789012)"
                match = re.search(r"(.*?) \(([A-F0-9-]+)\)", line)
                if match:
                    name = match.group(1).strip()
                    udid = match.group(2)
                    devices.append({
                        "serial": udid,
                        "name": name,
                        "platform": "ios",
                        "device_type": "simulator",
                        "status": "online"
                    })
            return devices
        except Exception:
            return []

    async def connect_android_device(self, serial: str) -> bool:
        """连接 Android 设备 (adb connect)"""
        try:
            result = subprocess.run(
                ["adb", "connect", serial],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "connected" in result.stdout.lower() or "already connected" in result.stdout.lower()
        except Exception:
            return False

    async def get_device_screenshot(self, serial: str, platform: str) -> Optional[bytes]:
        """获取设备截图"""
        try:
            if platform == "android":
                result = subprocess.run(
                    ["adb", "-s", serial, "exec-out", "screencap", "-p"],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0 and len(result.stdout) > 1000:
                    return result.stdout
            elif platform == "ios":
                result = subprocess.run(
                    ["xcrun", "simctl", "io", "booted", "screenshot"],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout
        except Exception:
            pass
        return None


def get_device_service() -> DeviceService:
    """获取设备服务实例"""
    return DeviceService()
