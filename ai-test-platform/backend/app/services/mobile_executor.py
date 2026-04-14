"""移动端测试执行引擎 - Appium"""
import asyncio
import json
import os
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import get_settings


@dataclass
class DeviceInfo:
    """设备信息"""
    udid: str
    platform: str  # android/ios
    name: str
    version: str
    status: str = "available"  # available/busy/offline
    host: str = "localhost"  # Appium 服务器地址


class MobileExecutor:
    """移动端测试执行引擎 - Appium"""

    def __init__(self):
        settings = get_settings()
        self.appium_host = settings.appium_host or "localhost"
        self.appium_port = settings.appium_port or "4723"
        self.android_sdk_path = settings.android_sdk_path or os.environ.get("ANDROID_HOME", "")
        self.ios_sdk_path = settings.ios_sdk_path or os.environ.get("DEVELOPER_DIR", "")

    async def execute_test(
        self,
        run_id: str,
        code_content: str,
        device: DeviceInfo,
        platform: str = "android"
    ) -> dict:
        """
        执行移动端测试

        Args:
            run_id: 测试运行ID
            code_content: Appium 测试代码 (Python)
            device: 目标设备信息
            platform: 平台类型 (android/ios)

        Returns:
            执行结果字典
        """
        # 创建临时目录
        test_dir = f"/tmp/mobile-test-{run_id}"
        os.makedirs(test_dir, exist_ok=True)

        test_file = f"{test_dir}/test_mobile.py"
        capabilities_file = f"{test_dir}/caps.json"

        try:
            # 1. 生成测试文件
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(code_content)

            # 2. 生成 capabilities
            caps = self._generate_capabilities(device, platform)
            with open(capabilities_file, "w", encoding="utf-8") as f:
                json.dump(caps, f, ensure_ascii=False, indent=2)

            # 3. 执行测试
            if platform == "android":
                result = await self._run_android_test(run_id, test_file, device)
            else:
                result = await self._run_ios_test(run_id, test_file, device)

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "logs": "",
            }
        finally:
            # 清理临时目录
            import shutil
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir, ignore_errors=True)

    def _generate_capabilities(self, device: DeviceInfo, platform: str) -> dict:
        """生成 Appium Capabilities"""
        if platform == "android":
            return {
                "platformName": "Android",
                "automationName": "UiAutomator2",
                "udid": device.udid,
                "deviceName": device.name,
                "platformVersion": device.version,
                "noReset": True,
                "disableWindowAnimation": True,
                "uiautomator2ServerLaunchTimeout": 60000,
                "uiautomator2ServerInstallTimeout": 120000,
            }
        else:  # ios
            return {
                "platformName": "iOS",
                "automationName": "XCUITest",
                "udid": device.udid,
                "deviceName": device.name,
                "platformVersion": device.version,
                "noReset": True,
                "useNewWDA": True,
                "wdaLocalPort": 8100,
            }

    async def _run_android_test(
        self,
        run_id: str,
        test_file: str,
        device: DeviceInfo
    ) -> dict:
        """运行 Android 测试"""
        start_time = datetime.now()
        logs = []
        exit_code = 0

        try:
            # 1. 确保 ADB 连接
            await self._ensure_adb_connection(device)

            # 2. 启动 Appium 会话（如果需要）
            appium_session = await self._start_appium_session(device)

            # 3. 执行测试
            cmd = [
                "python", test_file,
                "--appium-host", self.appium_host,
                "--appium-port", self.appium_port,
                "--udid", device.udid,
                "--platform", "android"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "ANDROID_HOME": self.android_sdk_path}
            )

            stdout, _ = await process.communicate()
            logs.append(stdout.decode('utf-8', errors='ignore'))
            exit_code = process.returncode

        except Exception as e:
            logs.append(f"Error running Android test: {str(e)}\n")
            exit_code = 1

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "status": "success" if exit_code == 0 else "failed",
            "exit_code": exit_code,
            "logs": "".join(logs),
            "duration_ms": duration_ms,
            "device_udid": device.udid,
            "platform": "android",
        }

    async def _run_ios_test(
        self,
        run_id: str,
        test_file: str,
        device: DeviceInfo
    ) -> dict:
        """运行 iOS 测试"""
        start_time = datetime.now()
        logs = []
        exit_code = 0

        try:
            # 1. 确保 iOS 设备连接
            await self._ensure_ios_device(device)

            # 2. 启动 WDA（WebDriverAgent）
            wda_session = await self._start_wda(device)

            # 3. 执行测试
            cmd = [
                "python", test_file,
                "--appium-host", self.appium_host,
                "--appium-port", self.appium_port,
                "--udid", device.udid,
                "--platform", "ios"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "DEVELOPER_DIR": self.ios_sdk_path}
            )

            stdout, _ = await process.communicate()
            logs.append(stdout.decode('utf-8', errors='ignore'))
            exit_code = process.returncode

        except Exception as e:
            logs.append(f"Error running iOS test: {str(e)}\n")
            exit_code = 1

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "status": "success" if exit_code == 0 else "failed",
            "exit_code": exit_code,
            "logs": "".join(logs),
            "duration_ms": duration_ms,
            "device_udid": device.udid,
            "platform": "ios",
        }

    async def _ensure_adb_connection(self, device: DeviceInfo) -> bool:
        """确保 ADB 连接"""
        try:
            # 检查设备是否已连接
            result = subprocess.run(
                ["adb", "-s", device.udid, "get-state"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip() == "device":
                return True

            # 尝试连接
            result = subprocess.run(
                ["adb", "connect", device.udid],
                capture_output=True,
                text=True
            )
            return "connected" in result.stdout.lower() or "already connected" in result.stdout.lower()
        except Exception:
            return False

    async def _ensure_ios_device(self, device: DeviceInfo) -> bool:
        """确保 iOS 设备连接"""
        try:
            result = subprocess.run(
                ["ideviceinfo", "-u", device.udid, "-k", "DeviceName"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _start_appium_session(self, device: DeviceInfo) -> Optional[str]:
        """启动 Appium 会话"""
        # Appium 服务器应该已经运行，这里只检查连接
        try:
            async with asyncio.timeout(5):
                reader, writer = await asyncio.open_connection(
                    self.appium_host,
                    int(self.appium_port)
                )
                writer.close()
                await writer.wait_closed()
                return None
        except Exception:
            # Appium 未运行，尝试启动
            return await self._launch_appium()

    async def _launch_appium(self) -> Optional[str]:
        """启动 Appium 服务器"""
        try:
            process = subprocess.Popen(
                ["appium", "--address", self.appium_host, "--port", self.appium_port, "--session-override"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await asyncio.sleep(5)  # 等待启动
            return str(process.pid)
        except Exception:
            return None

    async def _start_wda(self, device: DeviceInfo) -> Optional[str]:
        """启动 WebDriverAgent (iOS)"""
        try:
            # 使用 xcrun simctl 启动模拟器
            if "simulator" in device.udid.lower():
                subprocess.run(
                    ["xcrun", "simctl", "boot", device.udid],
                    capture_output=True
                )
            return None
        except Exception:
            return None

    async def list_devices(self, platform: Optional[str] = None) -> List[DeviceInfo]:
        """
        列出可用设备

        Args:
            platform: 过滤平台 (android/ios)

        Returns:
            设备列表
        """
        devices = []

        if platform is None or platform == "android":
            devices.extend(await self._list_android_devices())

        if platform is None or platform == "ios":
            devices.extend(await self._list_ios_devices())

        return devices

    async def _list_android_devices(self) -> List[DeviceInfo]:
        """列出 Android 设备"""
        devices = []
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split("\n")[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        udid = parts[0]
                        state = parts[1]
                        if state == "device":
                            # 获取设备信息
                            name = self._get_android_device_name(udid)
                            version = self._get_android_version(udid)
                            devices.append(DeviceInfo(
                                udid=udid,
                                platform="android",
                                name=name,
                                version=version,
                                status="available"
                            ))
        except Exception:
            pass
        return devices

    def _get_android_device_name(self, udid: str) -> str:
        """获取 Android 设备名称"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "Unknown"
        except Exception:
            return "Unknown"

    def _get_android_version(self, udid: str) -> str:
        """获取 Android 版本"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "getprop", "ro.build.version.release"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "Unknown"
        except Exception:
            return "Unknown"

    async def _list_ios_devices(self) -> List[DeviceInfo]:
        """列出 iOS 设备"""
        devices = []
        try:
            # 列出真机
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True,
                text=True
            )
            for udid in result.stdout.strip().split("\n"):
                if udid.strip():
                    name = self._get_ios_device_name(udid)
                    version = self._get_ios_version(udid)
                    devices.append(DeviceInfo(
                        udid=udid.strip(),
                        platform="ios",
                        name=name,
                        version=version,
                        status="available"
                    ))

            # 列出模拟器
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split("\n"):
                if "iPhone" in line or "iPad" in line:
                    parts = line.split("(")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        udid = parts[1].replace(")", "").strip()
                        version = self._get_simulator_version(name)
                        devices.append(DeviceInfo(
                            udid=udid,
                            platform="ios",
                            name=name,
                            version=version,
                            status="available"
                        ))
        except Exception:
            pass
        return devices

    def _get_ios_device_name(self, udid: str) -> str:
        """获取 iOS 设备名称"""
        try:
            result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "DeviceName"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "Unknown iPhone"
        except Exception:
            return "Unknown iPhone"

    def _get_ios_version(self, udid: str) -> str:
        """获取 iOS 版本"""
        try:
            result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "ProductVersion"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "Unknown"
        except Exception:
            return "Unknown"

    def _get_simulator_version(self, name: str) -> str:
        """获取模拟器版本"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split("\n"):
                if name in line and "(" in line:
                    version = line.split("(")[1].split(")")[0]
                    return version
            return "16.0"  # 默认
        except Exception:
            return "16.0"


# 全局单例
_executor: Optional[MobileExecutor] = None


def get_mobile_executor() -> MobileExecutor:
    """获取移动端执行器实例"""
    global _executor
    if _executor is None:
        _executor = MobileExecutor()
    return _executor
