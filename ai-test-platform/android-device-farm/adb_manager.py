"""Android 设备管理 - ADB"""
import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime


@dataclass
class AndroidDevice:
    """Android 设备信息"""
    udid: str
    name: str
    version: str
    status: str  # online/offline
    ip: Optional[str] = None
    port: int = 5555
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial: Optional[str] = None
    capabilities: dict = field(default_factory=dict)

    @property
    def is_connected(self) -> bool:
        return self.status == "device"

    @property
    def is_wifi(self) -> bool:
        return self.ip is not None


class ADBManager:
    """ADB 设备管理器"""

    def __init__(self):
        self._devices_cache: List[AndroidDevice] = []
        self._last_refresh: Optional[datetime] = None

    def list_devices(self, refresh: bool = False) -> List[AndroidDevice]:
        """
        列出所有连接的 Android 设备

        Args:
            refresh: 是否强制刷新缓存

        Returns:
            设备列表
        """
        if not refresh and self._devices_cache:
            return self._devices_cache

        result = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True
        )

        devices = []
        for line in result.stdout.strip().split("\n")[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    udid = parts[0]
                    status = parts[1]

                    # 解析设备信息
                    info = self._parse_device_info(udid)
                    model = self._get_device_prop(udid, "ro.product.model")
                    manufacturer = self._get_device_prop(udid, "ro.product.manufacturer")
                    version = self._get_device_prop(udid, "ro.build.version.release")

                    # 判断是否通过网络连接
                    ip = None
                    if ":" in udid and "." in udid.split(":")[0]:
                        ip = udid.split(":")[0]

                    devices.append(AndroidDevice(
                        udid=udid,
                        name=model or "Unknown",
                        version=version or "Unknown",
                        status=status,
                        ip=ip,
                        model=model,
                        manufacturer=manufacturer,
                        serial=udid.split(":")[0] if ":" in udid else udid,
                        capabilities=info
                    ))

        self._devices_cache = devices
        self._last_refresh = datetime.now()
        return devices

    def _parse_device_info(self, udid: str) -> dict:
        """解析设备详细信息"""
        info = {}
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "getprop"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if ":" in line:
                    match = re.match(r'\[(.+?)\]: \[(.+?)\]', line)
                    if match:
                        key, value = match.groups()
                        if value.strip():
                            info[key] = value.strip()
        except Exception:
            pass
        return info

    def _get_device_prop(self, udid: str, prop: str) -> Optional[str]:
        """获取设备系统属性"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "getprop", prop],
                capture_output=True,
                text=True,
                timeout=3
            )
            value = result.stdout.strip()
            return value if value else None
        except Exception:
            return None

    def get_device(self, udid: str) -> Optional[AndroidDevice]:
        """获取指定设备信息"""
        devices = self.list_devices()
        for device in devices:
            if device.udid == udid or device.serial == udid:
                return device
        return None

    def connect_wifi(self, ip: str, port: int = 5555) -> Tuple[bool, str]:
        """
        通过网络连接设备

        Args:
            ip: 设备 IP 地址
            port: 端口号，默认 5555

        Returns:
            (成功标志, 消息)
        """
        addr = f"{ip}:{port}"
        try:
            # 先断开现有连接
            subprocess.run(["adb", "disconnect", addr], capture_output=True)

            # 连接设备
            result = subprocess.run(
                ["adb", "connect", addr],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "connected" in result.stdout.lower() or "already connected" in result.stdout.lower():
                # 验证连接
                devices = self.list_devices(refresh=True)
                for device in devices:
                    if device.udid == addr:
                        return True, f"Successfully connected to {ip}:{port}"
                return True, f"Connected but device not in list"
            else:
                return False, result.stdout.strip()

        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, str(e)

    def disconnect_wifi(self, ip: str, port: int = 5555) -> Tuple[bool, str]:
        """断开网络连接"""
        addr = f"{ip}:{port}"
        try:
            result = subprocess.run(
                ["adb", "disconnect", addr],
                capture_output=True,
                text=True
            )
            return True, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def screenshot(self, udid: str, output_path: str) -> Tuple[bool, str]:
        """
        截图

        Args:
            udid: 设备 UDID
            output_path: 输出文件路径

        Returns:
            (成功标志, 消息/路径)
        """
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "exec-out", "screenshot"],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                with open(output_path, "wb") as f:
                    f.write(result.stdout)
                return True, output_path
            else:
                return False, "Screenshot failed"
        except Exception as e:
            return False, str(e)

    def install_app(self, udid: str, apk_path: str, grant_permissions: bool = True) -> Tuple[bool, str]:
        """
        安装应用

        Args:
            udid: 设备 UDID
            apk_path: APK 文件路径
            grant_permissions: 是否授予权限

        Returns:
            (成功标志, 消息)
        """
        try:
            cmd = ["adb", "-s", udid, "install"]
            if grant_permissions:
                cmd.append("-g")
            cmd.append(apk_path)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and "Success" in result.stdout:
                return True, "App installed successfully"
            else:
                return False, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Installation timeout"
        except Exception as e:
            return False, str(e)

    def uninstall_app(self, udid: str, package_name: str) -> Tuple[bool, str]:
        """卸载应用"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "uninstall", package_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, "App uninstalled successfully"
            return False, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def start_activity(self, udid: str, activity: str) -> Tuple[bool, str]:
        """启动 Activity"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "am", "start", "-n", activity],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, "Activity started"
            return False, result.stderr.strip() or result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def get_screen_size(self, udid: str) -> Optional[Tuple[int, int]]:
        """获取屏幕分辨率"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "wm", "size"],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout.strip()
            # 格式: Physical size: 1080x1920 或 Override size: 1080x1920
            match = re.search(r'(\d+)x(\d+)', output)
            if match:
                return int(match.group(1)), int(match.group(2))
        except Exception:
            pass
        return None

    def is_device_busy(self, udid: str) -> bool:
        """检查设备是否忙碌（用于 Appium 锁定）"""
        devices = self.list_devices()
        for device in devices:
            if device.udid == udid:
                # 可以通过 adb get-state 检查
                try:
                    result = subprocess.run(
                        ["adb", "-s", udid, "get-state"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    return "device" not in result.stdout.lower()
                except Exception:
                    return True
        return True

    def push_file(self, udid: str, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """推送文件到设备"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "push", local_path, remote_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, f"Pushed to {remote_path}"
            return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def pull_file(self, udid: str, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """从设备拉取文件"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "pull", remote_path, local_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, f"Pulled to {local_path}"
            return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def clear_app_data(self, udid: str, package_name: str) -> Tuple[bool, str]:
        """清除应用数据"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "pm", "clear", package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, "App data cleared"
            return False, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def get_running_apps(self, udid: str) -> List[str]:
        """获取正在运行的应用包名"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "pm", "list", "packages"],
                capture_output=True,
                text=True,
                timeout=10
            )
            packages = []
            for line in result.stdout.strip().split("\n"):
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
            return packages
        except Exception:
            return []

    def forward_port(self, udid: str, local: int, remote: int) -> Tuple[bool, int]:
        """端口转发（用于 Appium USB 连接）"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "forward", f"tcp:{local}", f"tcp:{remote}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, local
            return False, 0
        except Exception:
            return False, 0

    def reverse_port(self, udid: str, remote: int, local: int) -> Tuple[bool, int]:
        """反向端口转发"""
        try:
            result = subprocess.run(
                ["adb", "-s", udid, "reverse", f"tcp:{remote}", f"tcp:{local}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, remote
            return False, 0
        except Exception:
            return False, 0


# 全局单例
_adb_manager: Optional[ADBManager] = None


def get_adb_manager() -> ADBManager:
    """获取 ADB 管理器单例"""
    global _adb_manager
    if _adb_manager is None:
        _adb_manager = ADBManager()
    return _adb_manager
