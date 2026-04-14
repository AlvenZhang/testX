"""测试代码生成服务"""
import json
from typing import Any, Dict, List, Optional

from .ai_service import AIService, get_ai_service


class CodeGenService:
    """测试代码生成服务"""

    def __init__(self):
        self.ai_service = get_ai_service()

    async def generate_test_code(
        self,
        test_cases: List[Dict[str, Any]],
        framework: str = "pytest",
        test_type: str = "api",
    ) -> str:
        """
        生成测试代码

        Args:
            test_cases: 测试用例列表
            framework: 测试框架 (pytest/unittest/pytest-html)
            test_type: 测试类型 (api/web/mobile)

        Returns:
            生成的测试代码
        """
        if test_type == "api":
            return await self._generate_api_test_code(test_cases, framework)
        elif test_type == "web":
            return await self._generate_web_test_code(test_cases, framework)
        elif test_type == "mobile":
            return await self._generate_mobile_test_code(test_cases, framework)
        else:
            return await self._generate_generic_test_code(test_cases, framework)

    async def _generate_api_test_code(
        self,
        test_cases: List[Dict[str, Any]],
        framework: str = "pytest",
    ) -> str:
        """生成 API 测试代码"""
        cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)

        prompt = f"""为以下 API 测试用例生成 pytest 测试代码：

测试用例：
{cases_json}

要求：
1. 使用 pytest 框架
2. 使用 httpx 进行 HTTP 请求
3. 每个测试用例对应一个测试函数
4. 包含断言验证响应状态码和返回数据
5. 代码需要可执行

返回完整的 Python 代码文件内容。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试开发工程师，擅长编写高质量的 API 自动化测试代码。"},
            {"role": "user", "content": prompt}
        ])
        return response

    async def _generate_web_test_code(
        self,
        test_cases: List[Dict[str, Any]],
        framework: str = "pytest",
    ) -> str:
        """生成 Web UI 测试代码"""
        cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)

        prompt = f"""为以下 Web UI 测试用例生成 pytest + Playwright 测试代码：

测试用例：
{cases_json}

要求：
1. 使用 pytest + Playwright 框架
2. 每个测试用例对应一个测试函数
3. 包含页面操作和断言验证
4. 支持截图功能
5. 代码需要可执行

返回完整的 Python 代码文件内容。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的 Web UI 测试开发工程师，擅长使用 Playwright 编写自动化测试代码。"},
            {"role": "user", "content": prompt}
        ])
        return response

    async def _generate_mobile_test_code(
        self,
        test_cases: List[Dict[str, Any]],
        framework: str = "pytest",
    ) -> str:
        """生成移动端测试代码"""
        cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)

        prompt = f"""为以下移动端测试用例生成 Appium Python 测试代码：

测试用例：
{cases_json}

要求：
1. 使用 Appium Python 客户端
2. 每个测试用例对应一个测试函数
3. 支持 Android 和 iOS
4. 包含元素定位和操作
5. 代码需要可执行

返回完整的 Python 代码文件内容。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的移动端测试开发工程师，擅长使用 Appium 编写自动化测试代码。"},
            {"role": "user", "content": prompt}
        ])
        return response

    async def _generate_generic_test_code(
        self,
        test_cases: List[Dict[str, Any]],
        framework: str = "pytest",
    ) -> str:
        """生成通用测试代码"""
        cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)

        prompt = f"""为以下测试用例生成 pytest 测试代码：

测试用例：
{cases_json}

要求：
1. 使用 pytest 框架
2. 每个测试用例对应一个测试函数
3. 包含断言验证
4. 代码需要可执行

返回完整的 Python 代码文件内容。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试开发工程师。"},
            {"role": "user", "content": prompt}
        ])
        return response

    async def generate_test_code_with_fix(
        self,
        test_cases: List[Dict[str, Any]],
        previous_code: Optional[str] = None,
        error_message: Optional[str] = None,
        framework: str = "pytest",
        test_type: str = "api",
    ) -> str:
        """生成测试代码，如果之前有错误则进行修复"""
        if previous_code and error_message:
            return await self._fix_and_regenerate(
                test_cases, previous_code, error_message, framework, test_type
            )
        return await self.generate_test_code(test_cases, framework, test_type)

    async def _fix_and_regenerate(
        self,
        test_cases: List[Dict[str, Any]],
        previous_code: str,
        error_message: str,
        framework: str,
        test_type: str,
    ) -> str:
        """修复并重新生成代码"""
        prompt = f"""之前的测试代码执行失败，请修复：

错误信息：
{error_message}

之前的代码：
{previous_code}

测试用例：
{json.dumps(test_cases, ensure_ascii=False, indent=2)}

请分析错误原因，修复代码，并返回完整的、可执行的 Python 测试代码。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试开发工程师，擅长修复测试代码问题。"},
            {"role": "user", "content": prompt}
        ])
        return response

    async def validate_test_code(self, code: str) -> Dict[str, Any]:
        """验证测试代码语法和结构"""
        try:
            import ast
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {"valid": False, "error": f"Syntax error: {str(e)}"}

    async def optimize_test_code(self, code: str) -> str:
        """优化测试代码"""
        prompt = f"""优化以下测试代码，提高可读性和可维护性：

{code}

要求：
1. 保持功能不变
2. 提取重复代码为辅助函数
3. 添加必要的注释
4. 优化断言消息

返回优化后的代码。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试开发工程师，擅长优化代码。"},
            {"role": "user", "content": prompt}
        ])
        return response


_code_gen_service: Optional[CodeGenService] = None


def get_code_gen_service() -> CodeGenService:
    """获取代码生成服务实例"""
    global _code_gen_service
    if _code_gen_service is None:
        _code_gen_service = CodeGenService()
    return _code_gen_service
