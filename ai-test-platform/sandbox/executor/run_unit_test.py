#!/usr/bin/env python3
"""
单元测试执行器
在 Docker 沙箱中执行 pytest 单元测试
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List


class UnitTestExecutor:
    """单元测试执行器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def discover_tests(self, path: str, pattern: str = "test_*.py") -> List[str]:
        """发现测试文件"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q", path],
                capture_output=True,
                text=True,
                timeout=30
            )
            tests = []
            for line in result.stdout.split("\n"):
                if "::" in line and "<Module" not in line:
                    tests.append(line.strip())
            return tests
        except Exception as e:
            print(f"Error discovering tests: {e}")
            return []

    def run_tests(
        self,
        path: str,
        pattern: str = "test_*.py",
        verbose: bool = True,
        json_report: bool = True
    ) -> Dict[str, Any]:
        """
        运行测试

        Args:
            path: 测试路径（文件或目录）
            pattern: 测试文件匹配模式
            verbose: 详细输出
            json_report: 生成 JSON 报告

        Returns:
            测试结果
        """
        cmd = [
            "python", "-m", "pytest",
            path,
            "-v" if verbose else "",
            "--json-report" if json_report else "",
            "--json-report-file=/app/report.json",
            "--tb=short",
            "-o", "json_path=/app/report.json"
        ]

        # 移除空字符串
        cmd = [c for c in cmd if c]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0,
        }

    def run_test_file(
        self,
        file_path: str,
        test_name: str = None
    ) -> Dict[str, Any]:
        """
        运行单个测试文件或测试函数

        Args:
            file_path: 测试文件路径
            test_name: 可选的测试函数名

        Returns:
            测试结果
        """
        cmd = [
            "python", "-m", "pytest",
            file_path,
            "-v",
            "--tb=short"
        ]

        if test_name:
            cmd.append(f"-k={test_name}")

        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return {
                "file": file_path,
                "test": test_name,
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_ms": duration_ms,
            }
        except subprocess.TimeoutExpired:
            return {
                "file": file_path,
                "test": test_name,
                "passed": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test timeout",
                "duration_ms": 300000,
            }
        except Exception as e:
            return {
                "file": file_path,
                "test": test_name,
                "passed": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_ms": 0,
            }

    def parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """解析 pytest 输出"""
        lines = output.split("\n")
        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0,
        }

        for line in lines:
            line = line.strip()
            if " passed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "passed":
                        try:
                            stats["passed"] = int(parts[i - 1])
                            stats["total"] += stats["passed"]
                        except (ValueError, IndexError):
                            pass
            elif " failed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "failed":
                        try:
                            stats["failed"] = int(parts[i - 1])
                            stats["total"] += stats["failed"]
                        except (ValueError, IndexError):
                            pass
            elif " skipped" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "skipped":
                        try:
                            stats["skipped"] = int(parts[i - 1])
                        except (ValueError, IndexError):
                            pass
            elif " error" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "error":
                        try:
                            stats["error"] = int(parts[i - 1])
                            stats["total"] += stats["error"]
                        except (ValueError, IndexError):
                            pass

        return stats


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Unit Test Executor")
    parser.add_argument("--input", "-i", help="Input JSON file with test config")
    parser.add_argument("--path", "-p", default="/app/tests", help="Test path")
    parser.add_argument("--output", "-o", default="/app/report.json", help="Output JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    executor = UnitTestExecutor()

    result = {
        "name": "Unit Tests",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
    }

    if args.input:
        # 从 JSON 文件读取配置
        with open(args.input, "r", encoding="utf-8") as f:
            config = json.load(f)
            test_path = config.get("path", args.path)
    else:
        test_path = args.path

    # 运行测试
    test_result = executor.run_tests(
        path=test_path,
        verbose=args.verbose
    )

    result.update({
        "end_time": datetime.now().isoformat(),
        "passed": test_result["passed"],
        "exit_code": test_result["exit_code"],
        "stdout": test_result["stdout"],
        "stderr": test_result["stderr"],
    })

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 输出摘要
    stats = executor.parse_pytest_output(test_result["stdout"])
    print(f"\n{'='*50}")
    print(f"Unit Test Results")
    print(f"Total: {stats['total']}, Passed: {stats['passed']}, Failed: {stats['failed']}")
    print(f"{'='*50}\n")

    sys.exit(0 if test_result["passed"] else 1)


if __name__ == "__main__":
    main()
