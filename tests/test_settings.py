import pytest


async def register_and_get_cookie(client):
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


@pytest.mark.asyncio
async def test_settings_page(client):
    await register_and_get_cookie(client)
    response = await client.get("/settings")
    assert response.status_code == 200
    assert "Settings" in response.text
    assert "testuser" in response.text
    assert "test@example.com" in response.text


@pytest.mark.asyncio
async def test_settings_requires_auth(client):
    response = await client.get("/settings", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_update_alert_preferences(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/settings/profile",
        data={
            "alert_email": "alerts@example.com",
            "email_alerts_enabled": "on",
        },
    )
    assert response.status_code == 200
    assert "Profile updated" in response.text


@pytest.mark.asyncio
async def test_change_password(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/settings/password",
        data={
            "current_password": "securepassword123",
            "new_password": "newpassword456",
            "new_password_confirm": "newpassword456",
        },
    )
    assert response.status_code == 200
    assert "Password changed" in response.text


@pytest.mark.asyncio
async def test_change_password_wrong_current(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/settings/password",
        data={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
            "new_password_confirm": "newpassword456",
        },
    )
    assert response.status_code == 422
    assert "incorrect" in response.text


@pytest.mark.asyncio
async def test_change_password_mismatch(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/settings/password",
        data={
            "current_password": "securepassword123",
            "new_password": "newpassword456",
            "new_password_confirm": "differentpassword",
        },
    )
    assert response.status_code == 422
    assert "do not match" in response.text


@pytest.mark.asyncio
async def test_regenerate_api_key(client):
    await register_and_get_cookie(client)

    # Get initial API key (verify settings page loads)
    await client.get("/settings")

    # Regenerate
    response = await client.post("/settings/api-key")
    assert response.status_code == 200
    assert "API key regenerated" in response.text
