import pytest
import re

from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.models import Monitor, User, Alert
from app.auth import hash_password
from tests.conftest import test_session


async def setup_user_and_monitor(client):
    """Helper: register user, create a monitor, return slug from detail page."""
    # Register
    response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", response.cookies.get("access_token"))

    # Create monitor
    await client.post(
        "/monitors/new",
        data={
            "name": "Ping Test Monitor",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )

    # Get slug from detail page
    detail = await client.get("/monitors/1")
    match = re.search(r"/ping/([a-f0-9-]{36})", detail.text)
    assert match, "Could not find ping slug in monitor detail page"
    return match.group(1)


@pytest.mark.asyncio
async def test_ping_get(client):
    slug = await setup_user_and_monitor(client)
    response = await client.get(f"/ping/{slug}")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_ping_post(client):
    slug = await setup_user_and_monitor(client)
    response = await client.post(f"/ping/{slug}")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_ping_not_found(client):
    response = await client.get("/ping/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.text == "Not Found"


@pytest.mark.asyncio
async def test_ping_updates_status(client):
    slug = await setup_user_and_monitor(client)

    # First ping should move from "new" to "up"
    await client.get(f"/ping/{slug}")

    # Check status on dashboard
    dashboard = await client.get("/dashboard")
    assert "Up" in dashboard.text


@pytest.mark.asyncio
async def test_ping_records_history(client):
    slug = await setup_user_and_monitor(client)

    # Send multiple pings
    await client.get(f"/ping/{slug}")
    await client.post(f"/ping/{slug}")
    await client.get(f"/ping/{slug}")

    # Check ping history
    detail = await client.get("/monitors/1")
    assert "3 total pings" in detail.text


@pytest.mark.asyncio
async def test_ping_paused_monitor(client):
    slug = await setup_user_and_monitor(client)

    # Pause the monitor
    await client.post("/monitors/1/pause", follow_redirects=False)

    # Ping should still return 200 but with "paused" message
    response = await client.get(f"/ping/{slug}")
    assert response.status_code == 200
    assert "paused" in response.text.lower()


@pytest.mark.asyncio
async def test_ping_no_auth_required(client):
    """Ping endpoint must work without any authentication."""
    slug = await setup_user_and_monitor(client)

    # Clear cookies to simulate unauthenticated request
    client.cookies.clear()

    response = await client.get(f"/ping/{slug}")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_ping_recovery_from_down():
    """When a 'down' monitor receives a ping, it should recover to 'up' and create a recovery alert."""
    async with test_session() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password"),
        )
        db.add(user)
        await db.flush()

        monitor = Monitor(
            user_id=user.id,
            name="Down Monitor",
            period=300,
            grace=60,
            status="down",
            last_ping_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(monitor)
        await db.commit()
        slug = monitor.slug

    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/ping/{slug}")
        assert response.status_code == 200
        assert response.text == "OK"

    async with test_session() as db:
        result = await db.execute(select(Monitor).where(Monitor.slug == slug))
        m = result.scalar_one()
        assert m.status == "up"
        assert m.last_ping_at is not None

        alerts = await db.execute(select(Alert).where(Alert.monitor_id == m.id))
        alert_list = alerts.scalars().all()
        assert any(a.alert_type == "up" for a in alert_list)
