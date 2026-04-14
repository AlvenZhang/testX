"""AI 代码修复服务 - 自动修复测试代码错误"""
import hashlib
import json
from typing import Any

from .ai_service import AIService


class CodeFixService:
    """AI 代码修复服务"""

    def __init__(self):
        self.ai_service = AIService()

    async def fix_test_code(
        self,
        failed_code: str,
        error_message: str,
        test_type: str = "api",
    ) -> dict[str, Any]:
        """
        分析测试失败原因并生成修复后的代码

        Args:
            failed_code: 失败的测试代码
            error_message: 错误信息
            test_type: 测试类型

        Returns:
            {
                "fixed_code": "修复后的代码",
                "explanation": "修复说明",
                "original_error": "原错误"
            }
        """
        prompt = f"""分析以下测试代码的错误并修复：

错误信息：
{error_message}

失败的测试代码：
{failed_code}

测试类型：{test_type}

请分析错误原因并生成修复后的代码。返回 JSON 格式：
{{
    "fixed_code": "修复后的完整代码",
    "explanation": "修复说明",
    "original_error": "错误原因分析"
}}
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试工程师，擅长修复测试代码问题。"},
            {"role": "user", "content": prompt}
        ])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "fixed_code": failed_code,
                "explanation": "无法解析AI响应",
                "original_error": error_message
            }

    async def suggest_fixes(
        self,
        code: str,
        test_type: str,
    ) -> list[str]:
        """获取代码改进建议"""
        prompt = f"""分析以下测试代码，提供改进建议：

测试代码：
{code}

测试类型：{test_type}

请提供具体的改进建议列表，以 JSON 数组格式返回，每个元素是一个建议。
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试工程师，擅长优化测试代码。"},
            {"role": "user", "content": prompt}
        ])

        try:
            suggestions = json.loads(response)
            if isinstance(suggestions, list):
                return suggestions
            return []
        except json.JSONDecodeError:
            return []

    def _generate_cache_key(self, code: str, error_message: str, test_type: str) -> str:
        """生成缓存 key"""
        content = f"{code}:{error_message}:{test_type}"
        return f"code_fix:{hashlib.md5(content.encode()).hexdigest()}"


def get_code_fix_service() -> CodeFixService:
    """获取代码修复服务实例"""
    return CodeFixService()
