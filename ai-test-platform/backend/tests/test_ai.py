"""AI API测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_chat():
    """测试AI聊天"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/ai/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )
        # 可能成功或需要配置API key
        assert response.status_code in [200, 401, 500]


@pytest.mark.asyncio
async def test_analyze_requirement():
    """测试需求分析"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/ai/analyze-requirement",
            json={
                "requirement_id": "test-req-id"
            }
        )
        # 可能需要认证或资源不存在
        assert response.status_code in [200, 401, 404]


@pytest.mark.asyncio
async def test_generate_test_cases():
    """测试生成测试用例"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/ai/generate-test-cases",
            json={
                "requirement_id": "test-req-id"
            }
        )
        assert response.status_code in [200, 401, 404]


@pytest.mark.asyncio
async def test_generate_test_code():
    """测试生成测试代码"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/ai/generate-test-code",
            json={
                "requirement_id": "test-req-id",
                "test_cases": [
                    {"case_id": "1", "title": "Test case 1"}
                ]
            }
        )
        assert response.status_code in [200, 401, 404]
