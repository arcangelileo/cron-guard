import pytest
import re


async def setup_user_and_monitor(client):
    """Helper: register user, create a monitor, return slug."""
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

    await client.post(
        "/monitors/new",
        data={
            "name": "Badge Test",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )

    detail = await client.get("/monitors/1")
    match = re.search(r"/ping/([a-f0-9-]{36})", detail.text)
    assert match
    return match.group(1)


@pytest.mark.asyncio
async def test_badge_svg(client):
    slug = await setup_user_and_monitor(client)
    response = await client.get(f"/badge/{slug}.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    assert "new" in response.text  # status should be "new"


@pytest.mark.asyncio
async def test_badge_json(client):
    slug = await setup_user_and_monitor(client)
    response = await client.get(f"/badge/{slug}.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Badge Test"
    assert data["status"] == "new"
    assert data["last_ping"] is None
    assert data["period"] == 3600


@pytest.mark.asyncio
async def test_badge_not_found(client):
    response = await client.get("/badge/00000000-0000-0000-0000-000000000000.svg")
    assert response.status_code == 404

    response = await client.get("/badge/00000000-0000-0000-0000-000000000000.json")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_badge_updates_after_ping(client):
    slug = await setup_user_and_monitor(client)

    # Ping the monitor
    await client.get(f"/ping/{slug}")

    # Badge should now show "up"
    response = await client.get(f"/badge/{slug}.json")
    data = response.json()
    assert data["status"] == "up"
    assert data["last_ping"] is not None
