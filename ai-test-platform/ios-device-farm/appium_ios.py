"""Appium iOS 测试服务"""
import asyncio
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .xcrun_manager import XCRunManager, get_xcrun_manager


@dataclass
class AppiumIOSSession:
    """Appium iOS 会话信息"""
    session_id: str
    udid: str
    capabilities: dict
    driver: Any = None
    started_at: datetime = field(default_factory=datetime.now)
    status: str = "running"  # running/completed/failed
    is_simulator: bool = True


class AppiumIOSService:
    """Appium iOS 测试服务"""

    def __init__(self):
        self.xcrun: XCRunManager = get_xcrun_manager()
        self.sessions: Dict[str, AppiumIOSSession] = {}
        self.appium_host = os.environ.get("APPIUM_HOST", "localhost")
        self.appium_port = int(os.environ.get("APPIUM_PORT", "4723"))
        self.wda_port = int(os.environ.get("WDA_PORT", "8100"))

    def _get_capabilities(self, udid: str, **kwargs) -> dict:
        """生成 Appium Capabilities"""
        device_info = self.xcrun.get_device(udid)

        caps = {
            "platformName": "iOS",
            "automationName": "XCUITest",
            "udid": udid,
            "deviceName": device_info.name if device_info else "iOS Device",
            "platformVersion": device_info.version if device_info else "Unknown",
            "noReset": kwargs.get("no_reset", True),
            "useNewWDA": kwargs.get("use_new_wda", True),
            "wdaLocalPort": self.wda_port,
            "derivedDataPath": f"/tmp/wda_{udid.replace('-', '')}",
        }

        # 模拟器特殊配置
        if device_info and device_info.is_simulator:
            caps["simulator"] = True
            caps["automationTraceTemplate"] = "/tmp/AutomationTrace.tracetemplate"

        # 添加自定义配置
        if kwargs.get("bundle_id"):
            caps["bundleId"] = kwargs["bundle_id"]
        if kwargs.get("app"):
            caps["app"] = kwargs["app"]
        if kwargs.get("wda_bundle_id"):
            caps["wdaBundleId"] = kwargs["wda_bundle_id"]
        if kwargs.get("mg_empty"):
            caps["mg-empty"] = kwargs["mg_empty"]

        return caps

    async def create_session(
        self,
        udid: str,
        **kwargs
    ) -> AppiumIOSSession:
        """
        创建 Appium 会话

        Args:
            udid: 设备 UDID
            **kwargs: 其他 capabilities

        Returns:
            Appium 会话信息
        """
        from appium import webdriver
        from appium.webdriver.webdriver import WebDriver

        session_id = str(uuid.uuid4())
        caps = self._get_capabilities(udid, **kwargs)

        # 确保设备存在
        device = self.xcrun.get_device(udid)
        if not device:
            raise RuntimeError(f"Device {udid} not found")

        # 如果是模拟器，确保已启动
        if device.is_simulator and device.status != "running":
            success, msg = self.xcrun.boot_device(udid)
            if not success:
                raise RuntimeError(f"Failed to boot simulator: {msg}")
            await asyncio.sleep(2)  # 等待启动完成

        try:
            # 创建 WebDriver
            driver = webdriver.Remote(
                f"http://{self.appium_host}:{self.appium_port}/wd/hub",
                desired_capabilities=caps
            )

            session = AppiumIOSSession(
                session_id=session_id,
                udid=udid,
                capabilities=caps,
                driver=driver,
                is_simulator=device.is_simulator
            )
            self.sessions[session_id] = session

            return session

        except Exception as e:
            raise RuntimeError(f"Failed to create Appium session: {str(e)}")

    async def close_session(self, session_id: str) -> bool:
        """关闭 Appium 会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            try:
                if session.driver:
                    session.driver.quit()
                session.status = "completed"
                return True
            except Exception:
                return False
            finally:
                del self.sessions[session_id]
        return False

    async def execute_test(
        self,
        udid: str,
        test_script: str,
        **kwargs
    ) -> dict:
        """
        执行 iOS UI 测试

        Args:
            udid: 设备 UDID
            test_script: Python 测试脚本
            **kwargs: 其他 capabilities

        Returns:
            测试结果
        """
        session = None
        result = {
            "status": "failed",
            "session_id": None,
            "duration_ms": 0,
            "error": None,
            "steps": [],
            "screenshots": [],
        }

        start_time = time.time()

        try:
            # 创建会话
            session = await self.create_session(udid, **kwargs)
            result["session_id"] = session.session_id

            # 将测试脚本写入临时文件
            test_file = f"/tmp/appium_ios_test_{session.session_id}.py"
            with open(test_file, "w") as f:
                f.write(test_script)

            # 在子进程中执行测试脚本
            proc = await asyncio.create_subprocess_exec(
                "python",
                test_file,
                "--session-id",
                session.session_id,
                "--host",
                self.appium_host,
                "--port",
                str(self.appium_port),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                result["status"] = "passed"
            else:
                result["error"] = stderr.decode() or stdout.decode()

            # 尝试解析输出中的步骤
            try:
                output_data = json.loads(stdout.decode())
                if isinstance(output_data, dict):
                    result["steps"] = output_data.get("steps", [])
                    result["screenshots"] = output_data.get("screenshots", [])
            except json.JSONDecodeError:
                pass

        except Exception as e:
            result["error"] = str(e)
        finally:
            if session:
                await self.close_session(session.session_id)

            # 清理临时文件
            if "test_file" in locals():
                try:
                    os.remove(test_file)
                except Exception:
                    pass

            result["duration_ms"] = int((time.time() - start_time) * 1000)

        return result

    async def find_element(
        self,
        session_id: str,
        by: str,
        value: str,
        timeout: int = 10
    ):
        """查找元素"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        driver = session.driver

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(driver, timeout)

        if by == "id":
            return wait.until(EC.presence_of_element_located((By.ID, value)))
        elif by == "xpath":
            return wait.until(EC.presence_of_element_located((By.XPATH, value)))
        elif by == "class":
            return wait.until(EC.presence_of_element_located((By.CLASS_NAME, value)))
        elif by == "accessibility_id":
            return wait.until(EC.presence_of_element_located((
                MobileBy.ACCESSIBILITY_ID, value
            )))
        elif by == "css":
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, value)))
        else:
            raise ValueError(f"Unknown locator: {by}")

    async def click(
        self,
        session_id: str,
        by: str,
        value: str,
        timeout: int = 10
    ):
        """点击元素"""
        element = await self.find_element(session_id, by, value, timeout)
        element.click()
        return element

    async def send_keys(
        self,
        session_id: str,
        by: str,
        value: str,
        text: str,
        timeout: int = 10
    ):
        """输入文本"""
        element = await self.find_element(session_id, by, value, timeout)
        element.send_keys(text)
        return element

    async def get_text(
        self,
        session_id: str,
        by: str,
        value: str,
        timeout: int = 10
    ) -> str:
        """获取元素文本"""
        element = await self.find_element(session_id, by, value, timeout)
        return element.text

    async def take_screenshot(self, session_id: str, save_path: Optional[str] = None) -> str:
        """截图"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        if save_path is None:
            save_path = f"/tmp/screenshot_ios_{session_id}_{int(time.time())}.png"

        session.driver.save_screenshot(save_path)
        return save_path

    async def get_page_source(self, session_id: str) -> str:
        """获取页面 XML 源码"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        return session.driver.page_source

    async def execute_script(self, session_id: str, script: str, *args):
        """执行 JavaScript"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        return session.driver.execute_script(script, *args)

    async def hide_keyboard(self, session_id: str):
        """隐藏键盘"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        try:
            session.driver.hide_keyboard()
        except Exception:
            pass

    async def swipe(
        self,
        session_id: str,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 1000
    ):
        """滑动"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        driver = session.driver

        # 使用 TouchAction
        from appium.webdriver.common.touch_action import TouchAction
        action = TouchAction(driver)
        action.press(x=start_x, y=start_y).wait(duration).move_to(
            x=end_x, y=end_y
        ).release()
        action.perform()

    async def tap(self, session_id: str, x: int, y: int):
        """点击坐标"""
        if session_id not in self.sessions:
            raise RuntimeError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        driver = session.driver

        from appium.webdriver.common.touch_action import TouchAction
        action = TouchAction(driver)
        action.tap(x=x, y=y).perform()

    def get_active_session(self, udid: str) -> Optional[AppiumIOSSession]:
        """获取设备的当前活跃会话"""
        for session in self.sessions.values():
            if session.udid == udid and session.status == "running":
                return session
        return None

    def list_sessions(self) -> List[AppiumIOSSession]:
        """列出所有会话"""
        return list(self.sessions.values())


# Selenium/Appium 需要这些导入
from selenium.webdriver.common.by import By
from appium.webdriver.common.mobileby import MobileBy


# 全局单例
_appium_ios: Optional[AppiumIOSService] = None


def get_appium_ios_service() -> AppiumIOSService:
    """获取 Appium iOS 服务单例"""
    global _appium_ios
    if _appium_ios is None:
        _appium_ios = AppiumIOSService()
    return _appium_ios
