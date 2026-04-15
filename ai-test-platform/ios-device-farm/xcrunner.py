"""XCUITest执行器 - 在iOS设备上执行XCUITest测试"""
import asyncio
import logging
import subprocess
import json
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class XCUITestResult:
    """XCUITest执行结果"""
    success: bool
    exit_code: int
    output: str
    error_output: str
    duration: float
    test_count: int
    failure_count: int


class XCUITestExecutor:
    """XCUITest测试执行器"""

    def __init__(self):
        self.device_udid: Optional[str] = None

    async def run_test(
        self,
        device_udid: str,
        app_path: str,
        test_bundle_path: str,
        test_class: Optional[str] = None,
        test_method: Optional[str] = None,
    ) -> XCUITestResult:
        """
        执行XCUITest测试

        Args:
            device_udid: 设备UDID
            app_path: 被测App路径
            test_bundle_path: 测试Bundle路径
            test_class: 可选，指定测试类
            test_method: 可选，指定测试方法

        Returns:
            执行结果
        """
        import time
        start_time = time.time()

        cmd = [
            "xcodebuild",
            "test",
            "-destination", f"id={device_udid}",
            "-app", app_path,
            "-testBundle", test_bundle_path,
        ]

        if test_class:
            cmd.extend(["-only-testing:", test_class])
        if test_method and test_class:
            cmd.extend([f"{test_class}/{test_method}"])

        cmd.extend([
            "-resultBundlePath", "/tmp/xcuitest_result",
            "-json",
        ])

        logger.info(f"Running XCUITest: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
            )

            duration = time.time() - start_time

            # 解析测试结果
            test_result = self._parse_test_result(result.stdout, result.stderr, duration)

            logger.info(
                f"XCUITest completed: {test_result.test_count} tests, "
                f"{test_result.failure_count} failures, exit code: {test_result.exit_code}"
            )

            return test_result

        except subprocess.TimeoutExpired:
            logger.error(f"XCUITest timed out after 600 seconds")
            return XCUITestResult(
                success=False,
                exit_code=-1,
                output="",
                error_output="Test execution timed out after 600 seconds",
                duration=600,
                test_count=0,
                failure_count=0,
            )
        except Exception as e:
            logger.error(f"XCUITest execution failed: {e}")
            return XCUITestResult(
                success=False,
                exit_code=-1,
                output="",
                error_output=str(e),
                duration=time.time() - start_time,
                test_count=0,
                failure_count=0,
            )

    def _parse_test_result(self, stdout: str, stderr: str, duration: float) -> XCUITestResult:
        """解析测试结果"""
        # 尝试从JSON输出中解析结果
        try:
            # 查找JSON输出
            json_lines = []
            in_json = False
            for line in stdout.split('\n'):
                if line.strip() == '{':
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if in_json and line.strip() == '}':
                    break

            if json_lines:
                json_output = '\n'.join(json_lines)
                data = json.loads(json_output)

                # 解析测试统计
                tests_count = 0
                failures_count = 0

                if 'testSummary' in data:
                    tests_count = data['testSummary'].get('testsCount', 0)
                    failures_count = data['testSummary'].get('failureCount', 0)

                return XCUITestResult(
                    success=failures_count == 0,
                    exit_code=0 if failures_count == 0 else 1,
                    output=stdout,
                    error_output=stderr,
                    duration=duration,
                    test_count=tests_count,
                    failure_count=failures_count,
                )
        except json.JSONDecodeError:
            pass

        # 回退方案：从文本输出中提取结果
        tests_count = stdout.count("Test Case '-[")
        failures_count = stdout.count("** TEST FAILED **")

        return XCUITestResult(
            success=failures_count == 0,
            exit_code=0 if failures_count == 0 else 1,
            output=stdout,
            error_output=stderr,
            duration=duration,
            test_count=tests_count,
            failure_count=failures_count,
        )

    async def install_app(self, device_udid: str, app_path: str) -> bool:
        """
        安装App到设备

        Args:
            device_udid: 设备UDID
            app_path: App路径

        Returns:
            是否安装成功
        """
        result = subprocess.run(
            ["xcrun", "simctl", "install", device_udid, app_path],
            capture_output=True,
            text=True,
        )
        success = result.returncode == 0
        if not success:
            logger.error(f"Failed to install app: {result.stderr}")
        return success

    async def uninstall_app(self, device_udid: str, bundle_id: str) -> bool:
        """
        从设备卸载App

        Args:
            device_udid: 设备UDID
            bundle_id: App Bundle ID

        Returns:
            是否卸载成功
        """
        result = subprocess.run(
            ["xcrun", "simctl", "uninstall", device_udid, bundle_id],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0


# 全局执行器实例
_global_executor: Optional[XCUITestExecutor] = None


def get_xcuitest_executor() -> XCUITestExecutor:
    """获取全局XCUITest执行器"""
    global _global_executor
    if _global_executor is None:
        _global_executor = XCUITestExecutor()
    return _global_executor
