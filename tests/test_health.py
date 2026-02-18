import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "CronGuard"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_version_format(client):
    response = await client.get("/health")
    data = response.json()
    assert data["version"] == "0.1.0"
