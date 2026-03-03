# tests/api/test_health.py
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
