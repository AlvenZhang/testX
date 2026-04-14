"""iOS 模拟器管理 - XCRun"""
import os
import plistlib
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class iOSDevice:
    """iOS 设备信息"""
    udid: str
    name: str
    version: str
    is_simulator: bool
    status: str = "shutdown"  # shutdown/booting/running
    sdk: Optional[str] = None
    runtime: Optional[str] = None
    capabilities: dict = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        return self.status == "running"


@dataclass
class SimulatorInfo:
    """模拟器信息"""
    name: str
    device_type: str  # iPhone, iPad
    version: str
    runtime: str
    udid: str


class XCRunManager:
    """XCRun 模拟器管理器"""

    def __init__(self):
        self._devices_cache: List[iOSDevice] = []
        self._last_refresh: Optional[datetime] = None

    def list_devices(self, refresh: bool = False) -> List[iOSDevice]:
        """
        列出所有 iOS 设备/模拟器

        Args:
            refresh: 是否强制刷新缓存

        Returns:
            设备列表
        """
        if not refresh and self._devices_cache:
            return self._devices_cache

        devices = []

        # 列出真机
        devices.extend(self._list_physical_devices())

        # 列出模拟器
        devices.extend(self._list_simulators())

        self._devices_cache = devices
        self._last_refresh = datetime.now()
        return devices

    def _list_physical_devices(self) -> List[iOSDevice]:
        """列出真机设备"""
        devices = []
        try:
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )

            for udid in result.stdout.strip().split("\n"):
                if udid.strip():
                    info = self._get_device_info(udid.strip())
                    name = info.get("DeviceName", "Unknown iPhone")
                    version = info.get("ProductVersion", "Unknown")

                    devices.append(iOSDevice(
                        udid=udid.strip(),
                        name=name,
                        version=version,
                        is_simulator=False,
                        status="connected"
                    ))
        except FileNotFoundError:
            # idevice_id not found, likely not on macOS or not installed
            pass
        except Exception:
            pass

        return devices

    def _list_simulators(self) -> List[iOSDevice]:
        """列出模拟器"""
        devices = []
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                capture_output=True,
                text=True,
                timeout=15
            )

            current_device = None
            for line in result.stdout.strip().split("\n"):
                line = line.strip()

                # 解析模拟器列表
                if "(" in line and ")" in line:
                    # 格式: "iPhone 15 Pro (16.0)" 或 "iPhone 15 (Grouped)"
                    match = re.match(r"(.+?)\s+\((.+?)\)", line)
                    if match:
                        name = match.group(1).strip()
                        version = match.group(2).strip()

                        # 尝试获取 UDID
                        udid = self._get_simulator_udid(name, version)
                        if udid:
                            devices.append(iOSDevice(
                                udid=udid,
                                name=name,
                                version=version,
                                is_simulator=True,
                                status="shutdown",
                                runtime=version
                            ))
        except Exception:
            pass

        return devices

    def _get_device_info(self, udid: str) -> dict:
        """获取真机设备信息"""
        info = {}
        try:
            # 获取设备名称
            result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "DeviceName"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                info["DeviceName"] = result.stdout.strip()

            # 获取系统版本
            result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "ProductVersion"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                info["ProductVersion"] = result.stdout.strip()

            # 获取产品类型
            result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "ProductType"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                info["ProductType"] = result.stdout.strip()

        except Exception:
            pass

        return info

    def _get_simulator_udid(self, name: str, version: str) -> Optional[str]:
        """获取模拟器 UDID"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                capture_output=True,
                text=True,
                timeout=15
            )

            # 解析输出找到匹配的模拟器
            lines = result.stdout.strip().split("\n")
            for i, line in enumerate(lines):
                if name in line and f"({version})" in line:
                    # 尝试从后续行获取 UDID
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith("UUID:"):
                            return next_line.replace("UUID: ", "").strip()
        except Exception:
            pass
        return None

    def get_device(self, udid: str) -> Optional[iOSDevice]:
        """获取指定设备信息"""
        devices = self.list_devices()
        for device in devices:
            if device.udid == udid:
                return device
        return None

    def boot_device(self, udid: str) -> Tuple[bool, str]:
        """
        启动模拟器/设备

        Args:
            udid: 设备 UDID

        Returns:
            (成功标志, 消息)
        """
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                # 启动模拟器
                result = subprocess.run(
                    ["xcrun", "simctl", "boot", udid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    device.status = "running"
                    return True, f"Simulator {device.name} booted"
                return False, result.stderr.strip()
            else:
                # 真机需要通过 idevicepair 配对
                result = subprocess.run(
                    ["idevicepair", "pair", udid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return True, f"Device {device.name} paired"
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def shutdown_device(self, udid: str) -> Tuple[bool, str]:
        """关闭模拟器"""
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                result = subprocess.run(
                    ["xcrun", "simctl", "shutdown", udid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    device.status = "shutdown"
                    return True, f"Simulator {device.name} shutdown"
                return False, result.stderr.strip()
            else:
                return False, "Cannot shutdown physical devices"

        except Exception as e:
            return False, str(e)

    def install_app(self, udid: str, app_path: str) -> Tuple[bool, str]:
        """
        安装应用到模拟器/设备

        Args:
            udid: 设备 UDID
            app_path: .app 目录路径

        Returns:
            (成功标志, 消息)
        """
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                result = subprocess.run(
                    ["xcrun", "simctl", "install", udid, app_path],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                result = subprocess.run(
                    ["ideviceinstaller", "-u", udid, "-i", app_path],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

            if result.returncode == 0:
                return True, "App installed successfully"
            return False, result.stderr.strip() or result.stdout.strip()

        except Exception as e:
            return False, str(e)

    def uninstall_app(self, udid: str, bundle_id: str) -> Tuple[bool, str]:
        """卸载应用"""
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                result = subprocess.run(
                    ["xcrun", "simctl", "uninstall", udid, bundle_id],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                result = subprocess.run(
                    ["ideviceinstaller", "-u", udid, "-U", bundle_id],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

            if result.returncode == 0:
                return True, "App uninstalled successfully"
            return False, result.stderr.strip() or result.stdout.strip()

        except Exception as e:
            return False, str(e)

    def launch_app(self, udid: str, bundle_id: str) -> Tuple[bool, str]:
        """启动应用"""
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                # 使用 simctl launch
                result = subprocess.run(
                    ["xcrun", "simctl", "launch", udid, bundle_id],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # 使用 ideviceentreer
                result = subprocess.run(
                    ["ideviceenter", udid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                # 然后使用 launch 命令
                result = subprocess.run(
                    ["idevice-app-run", "-u", udid, bundle_id],
                    capture_output=True,
                    text=True,
                    timeout=30
                ) if result.returncode == 0 else result

            if result.returncode == 0:
                return True, f"App {bundle_id} launched"
            return False, result.stderr.strip() or result.stdout.strip()

        except Exception as e:
            return False, str(e)

    def screenshot(self, udid: str, output_path: str) -> Tuple[bool, str]:
        """截图"""
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                result = subprocess.run(
                    ["xcrun", "simctl", "io", udid, "screenshot", output_path],
                    capture_output=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ["idevicescreenshot", "-u", udid, output_path],
                    capture_output=True,
                    timeout=30
                )

            if result.returncode == 0:
                return True, output_path
            return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def get_apps(self, udid: str) -> List[str]:
        """获取已安装应用列表"""
        try:
            device = self.get_device(udid)
            if not device:
                return []

            if device.is_simulator:
                # 模拟器需要通过 simctl
                result = subprocess.run(
                    ["xcrun", "simctl", "listapps", udid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ["ideviceinstaller", "-u", udid, "-l"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            apps = []
            for line in result.stdout.strip().split("\n"):
                if line.startswith("- "):
                    apps.append(line.replace("- ", "").strip())

            return apps

        except Exception:
            return []

    def clear_keychain(self, udid: str) -> Tuple[bool, str]:
        """清除钥匙串"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "keychain", udid, "reset"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, "Keychain cleared"
            return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def open_url(self, udid: str, url: str) -> Tuple[bool, str]:
        """打开 URL"""
        try:
            device = self.get_device(udid)
            if not device:
                return False, f"Device {udid} not found"

            if device.is_simulator:
                result = subprocess.run(
                    ["xcrun", "simctl", "openurl", udid, url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ["ideviceopen", "-u", udid, "-u", url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            if result.returncode == 0:
                return True, f"Opened {url}"
            return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def get_log(self, udid: str, output_path: str) -> Tuple[bool, str]:
        """获取设备日志"""
        try:
            result = subprocess.run(
                ["idevicesyslog", "-u", udid],
                capture_output=True,
                timeout=30
            )
            with open(output_path, "wb") as f:
                f.write(result.stdout)
            return True, output_path
        except Exception as e:
            return False, str(e)


# 全局单例
_xcrun_manager: Optional[XCRunManager] = None


def get_xcrun_manager() -> XCRunManager:
    """获取 XCRun 管理器单例"""
    global _xcrun_manager
    if _xcrun_manager is None:
        _xcrun_manager = XCRunManager()
    return _xcrun_manager
