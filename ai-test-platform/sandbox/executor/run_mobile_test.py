#!/usr/bin/env python3
"""
移动端测试执行器
在 Docker 沙箱中执行 Appium 移动端测试
"""
import argparse
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# 优先尝试导入 Appium
try:
    from appium import webdriver
    from appium.webdriver.webdriver import WebDriver
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False


class MobileTestExecutor:
    """移动端测试执行器"""

    def __init__(self, host: str = "localhost", port: int = 4723):
        self.host = host
        self.port = port
        self.driver: Optional[WebDriver] = None

    def connect(self, caps: Dict[str, Any]) -> bool:
        """连接到 Appium 服务器"""
        if not APPIUM_AVAILABLE:
            print("ERROR: Appium not installed")
            return False

        try:
            self.driver = webdriver.Remote(
                f"http://{self.host}:{self.port}/wd/hub",
                desired_capabilities=caps
            )
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect to Appium: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def execute_steps(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行测试步骤"""
        if not self.driver:
            return {"status": "error", "error": "Not connected"}

        results = []
        all_passed = True

        for i, step in enumerate(steps):
            result = self._execute_step(step)
            result["step_index"] = i
            results.append(result)
            if not result.get("passed", False):
                all_passed = False
                # 遇到失败可以选择停止，这里选择继续
                # break

        return {
            "status": "passed" if all_passed else "failed",
            "results": results,
            "total": len(results),
            "passed": sum(1 for r in results if r.get("passed", False)),
            "failed": sum(1 for r in results if not r.get("passed", True)),
        }

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        action = step.get("action", "")
        result = {"action": action, "passed": False, "error": None}

        try:
            if action == "click":
                self._handle_click(step)
            elif action == "send_keys":
                self._handle_send_keys(step)
            elif action == "wait":
                time.sleep(step.get("seconds", 1))
            elif action == "screenshot":
                self._handle_screenshot(step)
            elif action == "swipe":
                self._handle_swipe(step)
            elif action == "tap":
                self._handle_tap(step)
            elif action == "back":
                self.driver.back()
            elif action == "home":
                self.driver.home()
            elif action == "refresh":
                self.driver.refresh()
            elif action == "get_text":
                result["text"] = self._handle_get_text(step)
            elif action == "is_displayed":
                result["displayed"] = self._handle_is_displayed(step)
            else:
                result["error"] = f"Unknown action: {action}"
                return result

            result["passed"] = True

        except Exception as e:
            result["passed"] = False
            result["error"] = str(e)

        return result

    def _find_element(self, by: str, value: str):
        """查找元素"""
        if by == "id":
            return self.driver.find_element("id", value)
        elif by == "xpath":
            return self.driver.find_element("xpath", value)
        elif by == "class":
            return self.driver.find_element("class name", value)
        elif by == "accessibility_id":
            return self.driver.find_element("accessibility id", value)
        else:
            raise ValueError(f"Unknown locator: {by}")

    def _handle_click(self, step: Dict[str, Any]):
        """处理点击"""
        by = step.get("by", "id")
        value = step.get("value", "")
        element = self._find_element(by, value)
        element.click()

    def _handle_send_keys(self, step: Dict[str, Any]):
        """处理输入文本"""
        by = step.get("by", "id")
        value = step.get("value", "")
        text = step.get("text", "")
        element = self._find_element(by, value)
        element.clear()
        element.send_keys(text)

    def _handle_screenshot(self, step: Dict[str, Any]):
        """处理截图"""
        path = step.get("path", f"/app/screenshot_{int(time.time())}.png")
        self.driver.save_screenshot(path)

    def _handle_swipe(self, step: Dict[str, Any]):
        """处理滑动"""
        start_x = step.get("start_x", 0)
        start_y = step.get("start_y", 0)
        end_x = step.get("end_x", 0)
        end_y = step.get("end_y", 0)
        duration = step.get("duration", 1000)

        from appium.webdriver.common.touch_action import TouchAction
        action = TouchAction(self.driver)
        action.press(x=start_x, y=start_y).wait(duration).move_to(
            x=end_x, y=end_y
        ).release().perform()

    def _handle_tap(self, step: Dict[str, Any]):
        """处理点击坐标"""
        x = step.get("x", 0)
        y = step.get("y", 0)

        from appium.webdriver.common.touch_action import TouchAction
        action = TouchAction(self.driver)
        action.tap(x=x, y=y).perform()

    def _handle_get_text(self, step: Dict[str, Any]) -> str:
        """获取文本"""
        by = step.get("by", "id")
        value = step.get("value", "")
        element = self._find_element(by, value)
        return element.text

    def _handle_is_displayed(self, step: Dict[str, Any]) -> bool:
        """检查元素是否显示"""
        by = step.get("by", "id")
        value = step.get("value", "")
        element = self._find_element(by, value)
        return element.is_displayed()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Mobile Test Executor")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with test steps")
    parser.add_argument("--output", "-o", default="/app/report.json", help="Output JSON file")
    parser.add_argument("--host", default="localhost", help="Appium host")
    parser.add_argument("--port", type=int, default=4723, help="Appium port")
    parser.add_argument("--caps", "-c", help="JSON string of capabilities")
    args = parser.parse_args()

    # 读取测试步骤
    with open(args.input, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    caps = json.loads(args.caps) if args.caps else test_data.get("capabilities", {})
    steps = test_data.get("steps", [])

    # 执行测试
    executor = MobileTestExecutor(host=args.host, port=args.port)

    result = {
        "name": test_data.get("name", "Mobile Test"),
        "start_time": datetime.now().isoformat(),
        "end_time": None,
    }

    try:
        if executor.connect(caps):
            exec_result = executor.execute_steps(steps)
            result.update(exec_result)
        else:
            result["status"] = "error"
            result["error"] = "Failed to connect to Appium"
    finally:
        executor.disconnect()
        result["end_time"] = datetime.now().isoformat()

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 输出摘要
    print(f"\n{'='*50}")
    print(f"Mobile Test: {result['name']}")
    print(f"Status: {result['status']}")
    print(f"Total: {result.get('total', 0)}, Passed: {result.get('passed', 0)}, Failed: {result.get('failed', 0)}")
    print(f"{'='*50}\n")

    sys.exit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
