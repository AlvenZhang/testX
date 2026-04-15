"""API测试执行器"""
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .utils import run_command, parse_junit_xml, save_test_results

logger = logging.getLogger(__name__)


def run_api_tests(
    code_content: str,
    base_url: str,
    output_dir: str = "/app/reports",
    run_id: Optional[str] = None,
    timeout: int = 300,
) -> Dict[str, Any]:
    """
    执行API测试

    Args:
        code_content: 测试代码内容
        base_url: API基础URL
        output_dir: 输出目录
        run_id: 执行ID
        timeout: 超时时间（秒）

    Returns:
        测试结果
    """
    import tempfile

    start_time = time.time()

    if not run_id:
        run_id = f"api_test_{int(start_time * 1000)}"

    logger.info(f"Starting API test execution: {run_id}")
    logger.info(f"Base URL: {base_url}")

    # 创建临时测试文件
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix="_test.py",
        dir="/app/tests",
        delete=False,
    ) as f:
        # 添加pytest配置
        f.write("import pytest\n")
        f.write("import httpx\n\n")
        f.write(f"BASE_URL = \"{base_url}\"\n\n")
        f.write(code_content)
        test_file = f.name

    logger.info(f"Test file created: {test_file}")

    try:
        # 执行测试
        result = run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--junitxml=/app/reports/junit.xml",
            ],
            cwd="/app",
            timeout=timeout,
        )

        # 解析结果
        junit_file = Path("/app/reports/junit.xml")
        if junit_file.exists():
            with open(junit_file, "r") as f:
                junit_content = f.read()
            test_results = parse_junit_xml(junit_content)
        else:
            test_results = {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "time": 0.0,
                "test_cases": [],
                "parse_error": "Junit XML not found",
            }

        duration = time.time() - start_time

        final_result = {
            "run_id": run_id,
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "duration_ms": int(duration * 1000),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "tests": test_results.get("tests", 0),
            "passed": test_results.get("tests", 0) - test_results.get("failures", 0) - test_results.get("errors", 0),
            "failed": test_results.get("failures", 0),
            "errors": test_results.get("errors", 0),
            "skipped": test_results.get("skipped", 0),
            "test_cases": test_results.get("test_cases", []),
        }

        # 保存结果
        result_file = save_test_results(final_result, output_dir, run_id)
        logger.info(f"Results saved to {result_file}")

        return final_result

    except Exception as e:
        logger.error(f"API test execution failed: {e}")
        duration = time.time() - start_time

        return {
            "run_id": run_id,
            "status": "error",
            "exit_code": -1,
            "duration_ms": int(duration * 1000),
            "error": str(e),
            "tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "skipped": 0,
            "test_cases": [],
        }

    finally:
        # 清理临时文件
        try:
            Path(test_file).unlink()
        except Exception:
            pass


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="API Test Executor")
    parser.add_argument("--code", type=str, required=True, help="Test code content")
    parser.add_argument("--base-url", type=str, required=True, help="API base URL")
    parser.add_argument("--run-id", type=str, help="Run ID")
    parser.add_argument("--output-dir", type=str, default="/app/reports", help="Output directory")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")

    args = parser.parse_args()

    result = run_api_tests(
        code_content=args.code,
        base_url=args.base_url,
        output_dir=args.output_dir,
        run_id=args.run_id,
        timeout=args.timeout,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
