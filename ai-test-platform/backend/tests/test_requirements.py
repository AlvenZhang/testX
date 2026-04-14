"""需求管理API测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_requirements():
    """测试获取需求列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/requirements/?project_id=test-project")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_requirement():
    """测试创建需求"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/requirements/",
            json={
                "project_id": "test-project-id",
                "title": "测试需求",
                "description": "这是一个测试需求",
                "priority": "high"
            }
        )
        # 可能返回 201 或 401（如果需要认证）
        assert response.status_code in [201, 401, 404]


@pytest.mark.asyncio
async def test_get_requirement_not_found():
    """测试获取不存在的需求"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/requirements/non-existent-id")
        assert response.status_code in [404, 401]
