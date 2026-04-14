#!/usr/bin/env python3
"""
API 测试执行器
在 Docker 沙箱中执行 API 测试
"""
import argparse
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx


class APIExecutor:
    """API 测试执行器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.results: List[Dict[str, Any]] = []

    def execute_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        执行单个 HTTP 请求

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他参数 (headers, json, params, etc.)

        Returns:
            执行结果
        """
        start_time = time.time()
        result = {
            "method": method,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "response": None,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)

                result.update({
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response": {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response.text[:10000],  # 限制响应体长度
                    }
                })
        except httpx.TimeoutException:
            result["error"] = f"Request timeout after {self.timeout}s"
        except httpx.RequestError as e:
            result["error"] = f"Request error: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个测试用例

        Args:
            test_case: 测试用例定义
                {
                    "name": "测试用例名称",
                    "request": {
                        "method": "GET/POST/PUT/DELETE",
                        "url": "https://api.example.com/endpoint",
                        "headers": {},
                        "json": {},
                        "params": {}
                    },
                    "assertions": [
                        {"type": "status_code", "expected": 200},
                        {"type": "jsonpath", "path": "$.code", "expected": 0},
                        {"type": "response_time", "max_ms": 1000}
                    ]
                }

        Returns:
            测试用例执行结果
        """
        test_result = {
            "name": test_case.get("name", "Unnamed Test"),
            "passed": False,
            "duration_ms": 0,
            "assertions": [],
            "error": None,
        }

        start_time = time.time()

        # 执行请求
        request_config = test_case.get("request", {})
        method = request_config.get("method", "GET").upper()
        url = request_config.get("url", "")

        request_kwargs = {}
        if "headers" in request_config:
            request_kwargs["headers"] = request_config["headers"]
        if "json" in request_config:
            request_kwargs["json"] = request_config["json"]
        if "params" in request_config:
            request_kwargs["params"] = request_config["params"]
        if "data" in request_config:
            request_kwargs["data"] = request_config["data"]

        request_result = self.execute_request(method, url, **request_kwargs)

        duration_ms = int((time.time() - start_time) * 1000)
        test_result["duration_ms"] = duration_ms

        # 执行断言
        all_assertions_passed = True
        for assertion in test_case.get("assertions", []):
            assertion_result = self._evaluate_assertion(assertion, request_result)
            test_result["assertions"].append(assertion_result)
            if not assertion_result["passed"]:
                all_assertions_passed = False

        # 如果请求失败，测试也失败
        if request_result.get("error"):
            test_result["error"] = request_result["error"]
            test_result["passed"] = False
        else:
            test_result["passed"] = all_assertions_passed

        return test_result

    def _evaluate_assertion(self, assertion: Dict[str, Any], request_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个断言"""
        assertion_type = assertion.get("type", "")

        result = {
            "type": assertion_type,
            "passed": False,
            "expected": assertion.get("expected"),
            "actual": None,
            "message": None,
        }

        try:
            if assertion_type == "status_code":
                expected = assertion.get("expected", 200)
                actual = request_result.get("status_code")
                result["passed"] = actual == expected
                result["actual"] = actual
                result["message"] = f"Status code: expected {expected}, got {actual}"

            elif assertion_type == "jsonpath":
                import jsonpath_ng
                expected = assertion.get("expected")
                jsonpath_expr = assertion.get("path", "")
                response_body = request_result.get("response", {}).get("body", "")

                try:
                    data = json.loads(response_body)
                    match = jsonpath_ng.parse(jsonpath_expr).find(data)
                    actual = match.value if match else None
                    result["passed"] = actual == expected
                    result["actual"] = actual
                    result["message"] = f"JSONPath {jsonpath_expr}: expected {expected}, got {actual}"
                except Exception as e:
                    result["passed"] = False
                    result["message"] = f"JSONPath error: {str(e)}"

            elif assertion_type == "response_time":
                max_ms = assertion.get("max_ms", 1000)
                actual = request_result.get("duration_ms", 0)
                result["passed"] = actual <= max_ms
                result["actual"] = actual
                result["message"] = f"Response time: expected <= {max_ms}ms, got {actual}ms"

            elif assertion_type == "body_contains":
                expected = assertion.get("expected", "")
                response_body = request_result.get("response", {}).get("body", "")
                result["passed"] = expected in response_body
                result["actual"] = response_body[:200]
                result["message"] = f"Body contains '{expected}': {result['passed']}"

            elif assertion_type == "header_exists":
                header_name = assertion.get("header", "")
                response_headers = request_result.get("response", {}).get("headers", {})
                result["passed"] = header_name.lower() in {k.lower(): v for k, v in response_headers.items()}
                result["actual"] = header_name in response_headers
                result["message"] = f"Header '{header_name}' exists: {result['passed']}"

            else:
                result["message"] = f"Unknown assertion type: {assertion_type}"

        except Exception as e:
            result["message"] = f"Assertion error: {str(e)}"

        return result

    def execute_test_suite(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整测试套件

        Args:
            test_suite: 测试套件定义
                {
                    "name": "API Test Suite",
                    "base_url": "https://api.example.com",
                    "test_cases": [...]
                }

        Returns:
            测试套件执行结果
        """
        suite_result = {
            "name": test_suite.get("name", "Unnamed Suite"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration_ms": 0,
            "test_results": [],
        }

        start_time = time.time()
        base_url = test_suite.get("base_url", "")

        for test_case in test_suite.get("test_cases", []):
            # 如果有 base_url，拼接完整 URL
            if base_url and not test_case.get("request", {}).get("url", "").startswith("http"):
                test_case["request"]["url"] = base_url + test_case["request"]["url"]

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
    parser = argparse.ArgumentParser(description="API Test Executor")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with test suite")
    parser.add_argument("--output", "-o", default="/app/report.json", help="Output JSON file")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Request timeout in seconds")
    args = parser.parse_args()

    # 读取测试套件
    with open(args.input, "r", encoding="utf-8") as f:
        test_suite = json.load(f)

    # 执行测试
    executor = APIExecutor(timeout=args.timeout)
    result = executor.execute_test_suite(test_suite)

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 输出摘要
    print(f"\n{'='*50}")
    print(f"Test Suite: {result['name']}")
    print(f"Total: {result['total']}, Passed: {result['passed']}, Failed: {result['failed']}")
    print(f"Duration: {result['duration_ms']}ms")
    print(f"{'='*50}\n")

    # 返回退出码
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
