"""AI 服务 - 对接豆包/火山引擎 API"""
import asyncio
import hashlib
import json
import httpx
import logging
import redis.asyncio as redis
from typing import Any, AsyncIterator, Optional

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务"""

    def __init__(self) -> None:
        settings = get_settings()
        self.provider = settings.ai_provider

        # 根据 provider 选择配置
        if self.provider == "minimax":
            self.api_key = settings.minimax_api_key
            self.model = settings.minimax_model
            self.base_url = settings.minimax_base_url
        elif self.provider == "ollama":
            self.api_key = ""  # Ollama 不需要 API key
            self.model = settings.ollama_model
            self.base_url = settings.ollama_base_url
        else:
            self.api_key = settings.ai_api_key
            self.model = settings.ai_model
            self.base_url = settings.ai_base_url

        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = 3600  # 缓存1小时

    async def _get_redis(self) -> Optional[redis.Redis]:
        """懒加载 Redis 客户端"""
        if self.redis_client is None:
            try:
                settings = get_settings()
                self.redis_client = redis.from_url(settings.redis_url, decode_responses=False)
                await self.redis_client.ping()
            except Exception:
                self.redis_client = None
        return self.redis_client

    def _generate_cache_key(self, messages: list[dict], temperature: float) -> str:
        """生成缓存 key"""
        content = f"{messages}:{temperature}"
        return f"ai:chat:{hashlib.md5(content.encode()).hexdigest()}"

    async def chat_with_cache(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> str:
        """带缓存的 chat"""
        if use_cache:
            cache_key = self._generate_cache_key(messages, temperature)
            redis_client = await self._get_redis()
            if redis_client:
                try:
                    cached = await redis_client.get(cache_key)
                    if cached:
                        return cached.decode() if isinstance(cached, bytes) else cached
                except Exception:
                    pass

        response = await self._chat_with_retry(messages, temperature)

        if use_cache and response:
            redis_client = await self._get_redis()
            if redis_client:
                try:
                    await redis_client.setex(cache_key, self.cache_ttl, response)
                except Exception:
                    pass

        return response

    async def _chat_with_retry(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_attempts: int = 3,
    ) -> str:
        """带指数退避的重试（处理 429/529 限流）"""
        for attempt in range(max_attempts):
            try:
                return await self.chat(messages, temperature)
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_msg = str(e)
                # 429 Too Many Requests, 529 Overloaded, 500 Server Error
                if status_code in (429, 529, 500) or "529" in error_msg or "500" in error_msg:
                    if attempt < max_attempts - 1:
                        delay = 2 ** attempt * 10
                        await asyncio.sleep(delay)
                        continue
                    raise
                raise
            except Exception as e:
                error_msg = str(e)
                # 处理未知状态码 529
                if "529" in error_msg and attempt < max_attempts - 1:
                    delay = 2 ** attempt * 10
                    await asyncio.sleep(delay)
                    continue
                if attempt == max_attempts - 1:
                    raise
                delay = 2 ** attempt
                await asyncio.sleep(delay)
        raise RuntimeError("chat_with_retry failed after all attempts")

    async def chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """发送对话请求"""
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        logger.info(f"AI request to {self.model} at {url}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.debug(f"AI response length: {len(content)} chars")
            return content

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """流式发送对话请求"""
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        logger.info(f"AI streaming request to {self.model}")

        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def analyze_requirement(self, requirement_title: str, requirement_description: str) -> dict[str, Any]:
        """分析需求，生成测试要点"""
        logger.info(f"Analyzing requirement: {requirement_title}")
        prompt = f"""分析以下需求，生成测试要点：

需求标题：{requirement_title}
需求描述：{requirement_description}

请以 JSON 格式返回测试要点，包含：
- test_points: 测试要点列表
- risk_points: 风险点列表
- suggested_test_types: 建议的测试类型（web/api/mobile）
"""
        response = await self.chat_with_cache([
            {"role": "system", "content": "你是一个专业的测试架构师。"},
            {"role": "user", "content": prompt}
        ])
        try:
            result = json.loads(response)
            logger.info(f"Requirement analysis complete: {len(result.get('test_points', []))} test points, {len(result.get('risk_points', []))} risk points")
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return {"test_points": [], "risk_points": [], "suggested_test_types": ["web"], "raw_response": response}

    async def generate_test_cases(
        self,
        requirement_title: str,
        requirement_description: str,
        test_types: list[str],
    ) -> list[dict]:
        """生成测试用例"""
        logger.info(f"Generating test cases for: {requirement_title}")
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
        response = await self.chat_with_cache([
            {"role": "system", "content": "你是一个专业的测试工程师。"},
            {"role": "user", "content": prompt}
        ])
        try:
            cases = json.loads(response)
            logger.info(f"Generated {len(cases)} test cases")
            return cases
        except json.JSONDecodeError:
            logger.warning("Failed to parse test cases as JSON")
            return []

    async def generate_test_code(self, test_cases: list[dict], framework: str = "pytest") -> str:
        """生成测试代码"""
        logger.info(f"Generating test code for {len(test_cases)} test cases using {framework}")
        cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)
        prompt = f"""根据以下测试用例生成 pytest 测试代码：

测试用例：
{cases_json}

使用 {framework} 框架，生成可执行的测试代码。
"""
        response = await self._chat_with_retry([
            {"role": "system", "content": "你是一个专业的测试开发工程师，擅长编写高质量的自动化测试代码。"},
            {"role": "user", "content": prompt}
        ])
        logger.info(f"Generated test code: {len(response)} chars")
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
        response = await self.chat_with_cache([
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
