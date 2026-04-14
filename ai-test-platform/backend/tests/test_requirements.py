"""需求管理API测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_requirement():
    """测试创建需求"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/requirements/",
            json={
                "project_id": "test-project-id",
                "title": "用户登录功能",
                "description": "支持邮箱密码登录",
                "priority": "high"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "用户登录功能"
        assert data["version"] == 1


@pytest.mark.asyncio
async def test_list_requirements():
    """测试获取需求列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/requirements/?project_id=test-project-id")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
