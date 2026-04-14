#!/usr/bin/env python3
"""
Web UI 测试执行器
在 Docker 沙箱中执行 Web UI 测试（Playwright/Selenium）
"""
import argparse
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# 优先使用 Playwright，fallback 到 Selenium
try:
    from playwright.sync_api import sync_playwright, Page, Browser, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class WebExecutor:
    """Web UI 测试执行器"""

    def __init__(self, browser: str = "chromium", headless: bool = True):
        self.browser = browser
        self.headless = headless
        self.results: List[Dict[str, Any]] = []

        if not PLAYWRIGHT_AVAILABLE and not SELENIUM_AVAILABLE:
            raise RuntimeError("Neither Playwright nor Selenium is available")

    # ==================== Playwright 实现 ====================

    def _create_playwright_browser(self):
        """创建 Playwright 浏览器"""
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=self.headless)
        return pw, browser

    def _execute_playwright_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """使用 Playwright 执行测试"""
        result = {
            "name": test_case.get("name", "Unnamed Test"),
            "passed": False,
            "duration_ms": 0,
            "error": None,
            "steps": [],
        }

        pw, browser = None, None
        start_time = time.time()

        try:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )
            page = context.new_page()

            # 执行测试步骤
            for step in test_case.get("steps", []):
                step_result = self._execute_playwright_step(page, step)
                result["steps"].append(step_result)
                if not step_result["passed"]:
                    result["passed"] = False
                    result["error"] = f"Step failed: {step_result.get('error', 'Unknown error')}"
                    break
            else:
                result["passed"] = True

        except Exception as e:
            result["passed"] = False
            result["error"] = str(e)
        finally:
            if browser:
                browser.close()
            if pw:
                pw.stop()

        result["duration_ms"] = int((time.time() - start_time) * 1000)
        return result

    def _execute_playwright_step(self, page: Page, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个 Playwright 步骤"""
        action = step.get("action", "")
        result = {"action": action, "passed": False, "error": None}

        try:
            if action == "goto":
                url = step.get("url", "")
                page.goto(url, wait_until=step.get("wait_until", "load"))
                result["passed"] = True

            elif action == "click":
                selector = step.get("selector", "")
                page.click(selector, timeout=step.get("timeout", 30000))
                result["passed"] = True

            elif action == "fill":
                selector = step.get("selector", "")
                value = step.get("value", "")
                page.fill(selector, value)
                result["passed"] = True

            elif action == "type":
                selector = step.get("selector", "")
                value = step.get("value", "")
                page.type(selector, value, delay=step.get("delay", 0))
                result["passed"] = True

            elif action == "select":
                selector = step.get("selector", "")
                value = step.get("value", "")
                page.select_option(selector, value)
                result["passed"] = True

            elif action == "wait_for_selector":
                selector = step.get("selector", "")
                timeout = step.get("timeout", 30000)
                page.wait_for_selector(selector, timeout=timeout)
                result["passed"] = True

            elif action == "wait_for_navigation":
                page.wait_for_load_state("networkidle")
                result["passed"] = True

            elif action == "screenshot":
                path = step.get("path", "/app/screenshot.png")
                page.screenshot(path=path)
                result["passed"] = True
                result["screenshot"] = path

            elif action == "assert_text":
                selector = step.get("selector", "")
                expected = step.get("expected", "")
                actual = page.text_content(selector)
                result["passed"] = expected in (actual or "")
                result["expected"] = expected
                result["actual"] = actual

            elif action == "assert_visible":
                selector = step.get("selector", "")
                result["passed"] = page.is_visible(selector)

            elif action == "assert_title":
                expected = step.get("expected", "")
                actual = page.title()
                result["passed"] = expected == actual
                result["expected"] = expected
                result["actual"] = actual

            elif action == "execute_script":
                script = step.get("script", "")
                page.evaluate(script)
                result["passed"] = True

            elif action == "hover":
                selector = step.get("selector", "")
                page.hover(selector)
                result["passed"] = True

            elif action == "press":
                selector = step.get("selector", "")
                key = step.get("key", "")
                page.press(selector, key)
                result["passed"] = True

            else:
                result["error"] = f"Unknown action: {action}"

        except Exception as e:
            result["passed"] = False
            result["error"] = str(e)

        return result

    # ==================== Selenium 实现 ====================

    def _create_selenium_driver(self) -> webdriver:
        """创建 Selenium WebDriver"""
        if self.browser == "chrome":
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            return webdriver.Chrome(options=options)
        elif self.browser == "firefox":
            options = webdriver.FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")
            return webdriver.Firefox(options=options)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

    def _execute_selenium_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """使用 Selenium 执行测试"""
        result = {
            "name": test_case.get("name", "Unnamed Test"),
            "passed": False,
            "duration_ms": 0,
            "error": None,
            "steps": [],
        }

        driver = None
        start_time = time.time()

        try:
            driver = self._create_selenium_driver()
            driver.set_window_size(1920, 1080)

            # 执行测试步骤
            for step in test_case.get("steps", []):
                step_result = self._execute_selenium_step(driver, step)
                result["steps"].append(step_result)
                if not step_result["passed"]:
                    result["passed"] = False
                    result["error"] = f"Step failed: {step_result.get('error', 'Unknown error')}"
                    break
            else:
                result["passed"] = True

        except Exception as e:
            result["passed"] = False
            result["error"] = str(e)
        finally:
            if driver:
                driver.quit()

        result["duration_ms"] = int((time.time() - start_time) * 1000)
        return result

    def _execute_selenium_step(self, driver: webdriver, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个 Selenium 步骤"""
        action = step.get("action", "")
        result = {"action": action, "passed": False, "error": None}

        try:
            if action == "goto":
                url = step.get("url", "")
                driver.get(url)
                result["passed"] = True

            elif action == "click":
                selector = step.get("selector", "")
                by = self._get_selenium_by(selector)
                element = WebDriverWait(driver, step.get("timeout", 30)).until(
                    EC.element_to_be_clickable(by)
                )
                element.click()
                result["passed"] = True

            elif action == "fill":
                selector = step.get("selector", "")
                value = step.get("value", "")
                by = self._get_selenium_by(selector)
                element = WebDriverWait(driver, step.get("timeout", 30)).until(
                    EC.presence_of_element_located(by)
                )
                element.clear()
                element.send_keys(value)
                result["passed"] = True

            elif action == "select":
                from selenium.webdriver.support.ui import Select
                selector = step.get("selector", "")
                value = step.get("value", "")
                by = self._get_selenium_by(selector)
                element = WebDriverWait(driver, step.get("timeout", 30)).until(
                    EC.presence_of_element_located(by)
                )
                Select(element).select_by_value(value)
                result["passed"] = True

            elif action == "wait_for_selector":
                selector = step.get("selector", "")
                by = self._get_selenium_by(selector)
                WebDriverWait(driver, step.get("timeout", 30)).until(
                    EC.presence_of_element_located(by)
                )
                result["passed"] = True

            elif action == "screenshot":
                path = step.get("path", "/app/screenshot.png")
                driver.save_screenshot(path)
                result["passed"] = True
                result["screenshot"] = path

            elif action == "assert_text":
                selector = step.get("selector", "")
                expected = step.get("expected", "")
                by = self._get_selenium_by(selector)
                element = WebDriverWait(driver, step.get("timeout", 30)).until(
                    EC.presence_of_element_located(by)
                )
                actual = element.text
                result["passed"] = expected in (actual or "")
                result["expected"] = expected
                result["actual"] = actual

            elif action == "assert_visible":
                selector = step.get("selector", "")
                by = self._get_selenium_by(selector)
                element = WebDriverWait(driver, step.get("timeout", 30)).until(
                    EC.presence_of_element_located(by)
                )
                result["passed"] = element.is_displayed()

            elif action == "assert_title":
                expected = step.get("expected", "")
                actual = driver.title
                result["passed"] = expected == actual
                result["expected"] = expected
                result["actual"] = actual

            else:
                result["error"] = f"Unknown action: {action}"

        except Exception as e:
            result["passed"] = False
            result["error"] = str(e)

        return result

    def _get_selenium_by(self, selector: str):
        """解析 Selenium 定位器"""
        if selector.startswith("id="):
            return By.ID, selector[3:]
        elif selector.startswith("name="):
            return By.NAME, selector[5:]
        elif selector.startswith("css="):
            return By.CSS_SELECTOR, selector[4:]
        elif selector.startswith("xpath="):
            return By.XPATH, selector[6:]
        elif selector.startswith("//"):
            return By.XPATH, selector
        else:
            return By.CSS_SELECTOR, selector

    # ==================== 统一接口 ====================

    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试用例（自动选择驱动）"""
        if PLAYWRIGHT_AVAILABLE:
            return self._execute_playwright_test(test_case)
        else:
            return self._execute_selenium_test(test_case)

    def execute_test_suite(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整测试套件"""
        suite_result = {
            "name": test_suite.get("name", "Unnamed Suite"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration_ms": 0,
            "test_results": [],
            "driver": "playwright" if PLAYWRIGHT_AVAILABLE else "selenium",
        }

        start_time = time.time()

        for test_case in test_suite.get("test_cases", []):
            result = self.execute_test_case(test_case)
            suite_result["test_results"].append(result)
            suite_result["total"] += 1
            if result["passed"]:
                suite_result["passed"] += 1
            else:
                suite_result["failed"] += 1

        suite_result["end_time"] = datetime.now().isoformat()
        suite_result["duration_ms"] = int((time.time() - start_time) * 1000)

        return suite_result


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Web UI Test Executor")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with test suite")
    parser.add_argument("--output", "-o", default="/app/report.json", help="Output JSON file")
    parser.add_argument("--browser", "-b", default="chromium", help="Browser to use (chromium/firefox)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    args = parser.parse_args()

    # 读取测试套件
    with open(args.input, "r", encoding="utf-8") as f:
        test_suite = json.load(f)

    # 执行测试
    executor = WebExecutor(browser=args.browser, headless=args.headless)
    result = executor.execute_test_suite(test_suite)

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 输出摘要
    print(f"\n{'='*50}")
    print(f"Test Suite: {result['name']}")
    print(f"Driver: {result['driver']}")
    print(f"Total: {result['total']}, Passed: {result['passed']}, Failed: {result['failed']}")
    print(f"Duration: {result['duration_ms']}ms")
    print(f"{'='*50}\n")

    # 返回退出码
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
