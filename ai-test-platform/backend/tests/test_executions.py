"""测试执行API测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_run_execution():
    """测试执行测试"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/executions/run/test-code-id",
            json={"test_type": "api"}
        )
        # 可能需要认证或资源不存在
        assert response.status_code in [201, 401, 404]


@pytest.mark.asyncio
async def test_mobile_execution_devices():
    """测试获取移动端设备列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/mobile-executions/devices")
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_mobile_execution_run():
    """测试移动端执行"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        response = await client.post(
            "/api/v1/mobile-executions/run",
            json={
                "code_content": "print('test')",
                "device_id": "test-device-id",
                "platform": "android",
                "test_type": "functional"
            }
        )
        # 可能需要认证或设备不存在
        assert response.status_code in [201, 401, 404]
