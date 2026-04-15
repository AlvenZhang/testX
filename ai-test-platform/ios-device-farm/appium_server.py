"""iOS Appium服务器管理 - 启动/停止Appium for iOS实例"""
import asyncio
import logging
import subprocess
import signal
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AppiumiOSConfig:
    """iOS Appium服务器配置"""
    port: int = 4723
    bootstrap_port: int = 4724
    wda_local_port: int = 8100
    use_new_wda: bool = True
    wda_bundle_id: str = "com.facebook.WebDriverAgentRunner"
    derived_data_path: Optional[str] = None
    log_level: str = "debug"
    session_override: bool = False


class AppiumiOSServer:
    """iOS Appium服务器"""

    def __init__(self, device_udid: str, is_simulator: bool = False, config: Optional[AppiumiOSConfig] = None):
        self.device_udid = device_udid
        self.is_simulator = is_simulator
        self.config = config or AppiumiOSConfig()
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None
        self.url = f"http://localhost:{self.config.port}/wd/hub"

    async def start(self) -> bool:
        """
        启动iOS Appium服务器

        Returns:
            是否启动成功
        """
        if self.process is not None:
            logger.warning(f"Appium iOS server for {self.device_udid} is already running")
            return True

        try:
            cmd = [
                "appium",
                "--port", str(self.config.port),
                "--bootstrap-port", str(self.config.bootstrap_port),
                "--webdriveragent-port", str(self.config.wda_local_port),
                "-U", self.device_udid,
                "--log-level", self.config.log_level,
                "--log-timestamp",
            ]

            # iOS特定参数
            if self.config.use_new_wda:
                cmd.extend(["--use-new-wda"])

            if self.config.derived_data_path:
                cmd.extend(["--derived-data-path", self.config.derived_data_path])

            if self.config.session_override:
                cmd.append("--session-override")

            if self.is_simulator:
                cmd.append("--simulator")

            logger.info(f"Starting iOS Appium server: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
            )

            await self._wait_for_server(timeout=60)

            self.started_at = datetime.utcnow()
            logger.info(f"iOS Appium server started at {self.url} for device {self.device_udid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start iOS Appium server: {e}")
            await self.stop()
            return False

    async def stop(self) -> bool:
        """
        停止iOS Appium服务器

        Returns:
            是否停止成功
        """
        if self.process is None:
            logger.warning(f"Appium iOS server for {self.device_udid} is not running")
            return True

        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            logger.info(f"iOS Appium server stopped for device {self.device_udid}")
            self.process = None
            self.started_at = None
            return True

        except Exception as e:
            logger.error(f"Error stopping iOS Appium server: {e}")
            return False

    async def restart(self) -> bool:
        """重启服务器"""
        await self.stop()
        await asyncio.sleep(2)
        return await self.start()

    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        return self.process is not None and self.process.poll() is None

    async def get_status(self) -> Dict:
        """获取服务器状态"""
        return {
            "device_udid": self.device_udid,
            "is_simulator": self.is_simulator,
            "running": self.is_running(),
            "url": self.url,
            "port": self.config.port,
            "wda_port": self.config.wda_local_port,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "pid": self.process.pid if self.process else None,
        }

    async def _wait_for_server(self, timeout: int = 60) -> bool:
        """等待服务器启动（iOS启动较慢）"""
        import httpx

        start_time = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    response = await client.get(f"{self.url}/status", timeout=5.0)
                    if response.status_code == 200:
                        return True
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(2)

        raise TimeoutError(f"iOS Appium server did not start within {timeout} seconds")


class AppiumiOSManager:
    """iOS Appium服务器管理器"""

    def __init__(self):
        self._servers: Dict[str, AppiumiOSServer] = {}
        self._lock = asyncio.Lock()

    async def start_server(
        self,
        device_udid: str,
        is_simulator: bool = False,
        config: Optional[AppiumiOSConfig] = None,
    ) -> AppiumiOSServer:
        """
        为iOS设备启动Appium服务器

        Args:
            device_udid: 设备UDID
            is_simulator: 是否为模拟器
            config: 服务器配置

        Returns:
            AppiumiOSServer实例
        """
        async with self._lock:
            if device_udid in self._servers:
                server = self._servers[device_udid]
                if server.is_running():
                    logger.info(f"iOS Appium server already running for device {device_udid}")
                    return server
                del self._servers[device_udid]

            server = AppiumiOSServer(device_udid, is_simulator, config)
            success = await server.start()

            if not success:
                raise RuntimeError(f"Failed to start iOS Appium server for device {device_udid}")

            self._servers[device_udid] = server
            logger.info(f"iOS Appium server started for device {device_udid}")
            return server

    async def stop_server(self, device_udid: str) -> bool:
        """停止设备的Appium服务器"""
        async with self._lock:
            server = self._servers.get(device_udid)
            if server is None:
                logger.warning(f"No iOS Appium server found for device {device_udid}")
                return True

            success = await server.stop()
            if success:
                del self._servers[device_udid]
            return success

    async def stop_all(self) -> None:
        """停止所有iOS Appium服务器"""
        async with self._lock:
            for device_udid in list(self._servers.keys()):
                server = self._servers[device_udid]
                await server.stop()
            self._servers.clear()
            logger.info("All iOS Appium servers stopped")

    def get_server(self, device_udid: str) -> Optional[AppiumiOSServer]:
        """获取设备的Appium服务器"""
        return self._servers.get(device_udid)

    def get_all_servers(self) -> Dict[str, AppiumiOSServer]:
        """获取所有服务器"""
        return self._servers.copy()

    async def get_all_status(self) -> list:
        """获取所有服务器状态"""
        return [await server.get_status() for server in self._servers.values()]


# 全局管理器实例
_global_ios_manager: Optional[AppiumiOSManager] = None


def get_ios_appium_manager() -> AppiumiOSManager:
    """获取全局iOS Appium服务器管理器"""
    global _global_ios_manager
    if _global_ios_manager is None:
        _global_ios_manager = AppiumiOSManager()
    return _global_ios_manager
