"""AI 服务 - 对接豆包/火山引擎 API"""
import httpx
from typing import Optional
import json

from ..core.config import get_settings


class AIService:
    """AI 服务"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ai_api_key
        self.model = settings.ai_model
        self.base_url = settings.ai_base_url

    async def chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """发送对话请求"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def analyze_requirement(self, requirement_title: str, requirement_description: str) -> dict:
        """分析需求，生成测试要点"""
        prompt = f"""分析以下需求，生成测试要点：

需求标题：{requirement_title}
需求描述：{requirement_description}

请以 JSON 格式返回测试要点，包含：
- test_points: 测试要点列表
- risk_points: 风险点列表
- suggested_test_types: 建议的测试类型（web/api/mobile）
"""
        response = await self.chat([
            {"role": "system", "content": "你是一个专业的测试架构师。"},
            {"role": "user", "content": prompt}
        ])
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"test_points": [], "risk_points": [], "suggested_test_types": ["web"], "raw_response": response}

    async def generate_test_cases(self, requirement_title: str, requirement_description: str, test_types: list[str]) -> list[dict]:
        """生成测试用例"""
        prompt = f"""为以下需求生成测试用例：

需求标题：{requirement_title}
需求描述：{requirement_description}
测试类型：{', '.join(test_types)}

请生成具体的测试用例，包含：
- 用例编号
- 用例标题
- 测试步骤
- 预期结果
- 优先级

以 JSON 数组格式返回。
"""
        response = await self.chat([
            {"role": "system", "content": "你是一个专业的测试工程师。"},
            {"role": "user", "content": prompt}
        ])
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    async def generate_test_code(self, test_cases: list[dict], framework: str = "pytest") -> str:
        """生成测试代码"""
        cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)
        prompt = f"""根据以下测试用例生成 pytest 测试代码：

测试用例：
{cases_json}

使用 {framework} 框架，生成可执行的测试代码。
"""
        response = await self.chat([
            {"role": "system", "content": "你是一个专业的测试开发工程师，擅长编写高质量的自动化测试代码。"},
            {"role": "user", "content": prompt}
        ])
        return response

    async def analyze_code_impact(self, code_changes: list[dict], requirements: list[dict]) -> list[dict]:
        """分析代码变更影响"""
        changes_json = json.dumps(code_changes, ensure_ascii=False, indent=2)
        requirements_json = json.dumps(requirements, ensure_ascii=False, indent=2)

        prompt = f"""分析以下代码变更对需求的影响：

代码变更：
{changes_json}

相关需求：
{requirements_json}

请返回受影响的的需求列表，以 JSON 数组格式。
"""
        response = await self.chat([
            {"role": "system", "content": "你是一个专业的测试架构师，擅长影响分析。"},
            {"role": "user", "content": prompt}
        ])
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []


def get_ai_service() -> AIService:
    """获取 AI 服务实例"""
    return AIService()
