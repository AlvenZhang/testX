"""Appium服务器管理 - 启动/停止Appium实例"""
import asyncio
import logging
import subprocess
import signal
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AppiumServerConfig:
    """Appium服务器配置"""
    port: int = 4723
    bootstrap_port: int = 4724
    chromedriver_port: int = 9500
    callback_port: int = 4725
    session_override: bool = False
    local_timezone: bool = True
    log_level: str = "debug"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    log_timestamp: bool = True


class AppiumServer:
    """Appium服务器"""

    def __init__(self, device_serial: str, config: Optional[AppiumServerConfig] = None):
        self.device_serial = device_serial
        self.config = config or AppiumServerConfig()
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None
        self.url = f"http://localhost:{self.config.port}/wd/hub"

    async def start(self) -> bool:
        """
        启动Appium服务器

        Returns:
            是否启动成功
        """
        if self.process is not None:
            logger.warning(f"Appium server for {self.device_serial} is already running")
            return True

        try:
            cmd = [
                "appium",
                "--port", str(self.config.port),
                "--bootstrap-port", str(self.config.bootstrap_port),
                "--chromedriver-port", str(self.config.chromedriver_port),
                "--callback-port", str(self.config.callback_port),
                "-U", self.device_serial,
                "--log-level", self.config.log_level,
                "--log-timestamp",
                "--local-timezone",
            ]

            if self.config.session_override:
                cmd.append("--session-override")

            logger.info(f"Starting Appium server: {' '.join(cmd)}")

            # 在后台启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
            )

            # 等待服务器启动
            await self._wait_for_server(timeout=30)

            self.started_at = datetime.utcnow()
            logger.info(f"Appium server started at {self.url} for device {self.device_serial}")
            return True

        except Exception as e:
            logger.error(f"Failed to start Appium server: {e}")
            await self.stop()
            return False

    async def stop(self) -> bool:
        """
        停止Appium服务器

        Returns:
            是否停止成功
        """
        if self.process is None:
            logger.warning(f"Appium server for {self.device_serial} is not running")
            return True

        try:
            # 发送终止信号
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            logger.info(f"Appium server stopped for device {self.device_serial}")
            self.process = None
            self.started_at = None
            return True

        except Exception as e:
            logger.error(f"Error stopping Appium server: {e}")
            return False

    async def restart(self) -> bool:
        """
        重启Appium服务器

        Returns:
            是否重启成功
        """
        await self.stop()
        await asyncio.sleep(2)  # 等待端口释放
        return await self.start()

    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        if self.process is None:
            return False
        return self.process.poll() is None

    async def get_status(self) -> Dict:
        """
        获取服务器状态

        Returns:
            状态信息
        """
        return {
            "device_serial": self.device_serial,
            "running": self.is_running(),
            "url": self.url,
            "port": self.config.port,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "pid": self.process.pid if self.process else None,
        }

    async def _wait_for_server(self, timeout: int = 30) -> bool:
        """等待服务器启动"""
        import httpx

        start_time = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    response = await client.get(f"{self.url}/status", timeout=2.0)
                    if response.status_code == 200:
                        return True
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(1)

        raise TimeoutError(f"Appium server did not start within {timeout} seconds")


class AppiumServerManager:
    """Appium服务器管理器"""

    def __init__(self):
        self._servers: Dict[str, AppiumServer] = {}
        self._lock = asyncio.Lock()

    async def start_server(self, device_serial: str, config: Optional[AppiumServerConfig] = None) -> AppiumServer:
        """
        为设备启动Appium服务器

        Args:
            device_serial: 设备序列号
            config: 服务器配置

        Returns:
            AppiumServer实例
        """
        async with self._lock:
            if device_serial in self._servers:
                server = self._servers[device_serial]
                if server.is_running():
                    logger.info(f"Appium server already running for device {device_serial}")
                    return server
                # 如果服务器已停止但还在字典中，先移除
                del self._servers[device_serial]

            server = AppiumServer(device_serial, config)
            success = await server.start()

            if not success:
                raise RuntimeError(f"Failed to start Appium server for device {device_serial}")

            self._servers[device_serial] = server
            logger.info(f"Appium server started for device {device_serial}")
            return server

    async def stop_server(self, device_serial: str) -> bool:
        """
        停止设备的Appium服务器

        Args:
            device_serial: 设备序列号

        Returns:
            是否成功停止
        """
        async with self._lock:
            server = self._servers.get(device_serial)
            if server is None:
                logger.warning(f"No Appium server found for device {device_serial}")
                return True

            success = await server.stop()
            if success:
                del self._servers[device_serial]
            return success

    async def stop_all(self) -> None:
        """停止所有Appium服务器"""
        async with self._lock:
            for device_serial in list(self._servers.keys()):
                server = self._servers[device_serial]
                await server.stop()
            self._servers.clear()
            logger.info("All Appium servers stopped")

    def get_server(self, device_serial: str) -> Optional[AppiumServer]:
        """获取设备的Appium服务器"""
        return self._servers.get(device_serial)

    def get_all_servers(self) -> Dict[str, AppiumServer]:
        """获取所有服务器"""
        return self._servers.copy()

    async def get_all_status(self) -> list:
        """获取所有服务器状态"""
        return [await server.get_status() for server in self._servers.values()]


# 全局管理器实例
_global_manager: Optional[AppiumServerManager] = None


def get_appium_manager() -> AppiumServerManager:
    """获取全局Appium服务器管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = AppiumServerManager()
    return _global_manager
