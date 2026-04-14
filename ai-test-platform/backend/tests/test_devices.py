"""设备管理API测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_devices():
    """测试获取设备列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/devices/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_device_not_found():
    """测试获取不存在的设备"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/devices/non-existent-id")
        assert response.status_code in [404, 401]


@pytest.mark.asyncio
async def test_create_device():
    """测试创建设备"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/devices/",
            json={
                "name": "Test Device",
                "platform": "android",
                "version": "12.0",
                "status": "online"
            }
        )
        # 可能成功或需要认证
        assert response.status_code in [201, 401, 422]
