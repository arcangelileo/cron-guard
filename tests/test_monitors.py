import pytest


async def register_and_get_cookie(client):
    """Helper to register a user and return the access token cookie."""
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
    token = response.cookies.get("access_token")
    client.cookies.set("access_token", token)
    return token


@pytest.mark.asyncio
async def test_dashboard_empty(client):
    await register_and_get_cookie(client)
    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "No monitors yet" in response.text


@pytest.mark.asyncio
async def test_new_monitor_page(client):
    await register_and_get_cookie(client)
    response = await client.get("/monitors/new")
    assert response.status_code == 200
    assert "Create New Monitor" in response.text


@pytest.mark.asyncio
async def test_create_monitor(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/monitors/new",
        data={
            "name": "Nightly Backup",
            "period": "86400",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"

    # Verify it appears on dashboard
    dashboard = await client.get("/dashboard")
    assert "Nightly Backup" in dashboard.text


@pytest.mark.asyncio
async def test_create_monitor_validation(client):
    await register_and_get_cookie(client)

    # Empty name
    response = await client.post(
        "/monitors/new",
        data={
            "name": "",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
    )
    assert response.status_code == 422

    # Period too small
    response = await client.post(
        "/monitors/new",
        data={
            "name": "Test Monitor",
            "period": "10",
            "grace": "0",
            "webhook_url": "",
        },
    )
    assert response.status_code == 422
    assert "at least 60 seconds" in response.text


@pytest.mark.asyncio
async def test_create_monitor_with_webhook(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/monitors/new",
        data={
            "name": "With Webhook",
            "period": "3600",
            "grace": "300",
            "webhook_url": "https://hooks.slack.com/services/test",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_create_monitor_invalid_webhook(client):
    await register_and_get_cookie(client)
    response = await client.post(
        "/monitors/new",
        data={
            "name": "Bad Webhook",
            "period": "3600",
            "grace": "0",
            "webhook_url": "not-a-url",
        },
    )
    assert response.status_code == 422
    assert "http://" in response.text


@pytest.mark.asyncio
async def test_monitor_detail_page(client):
    await register_and_get_cookie(client)

    # Create monitor
    await client.post(
        "/monitors/new",
        data={
            "name": "Test Monitor",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )

    # View detail
    response = await client.get("/monitors/1")
    assert response.status_code == 200
    assert "Test Monitor" in response.text
    assert "/ping/" in response.text
    assert "No pings received yet" in response.text


@pytest.mark.asyncio
async def test_edit_monitor(client):
    await register_and_get_cookie(client)

    # Create monitor
    await client.post(
        "/monitors/new",
        data={
            "name": "Original Name",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )

    # Edit page
    response = await client.get("/monitors/1/edit")
    assert response.status_code == 200
    assert "Edit Monitor" in response.text

    # Submit edit
    response = await client.post(
        "/monitors/1/edit",
        data={
            "name": "Updated Name",
            "period": "86400",
            "grace": "600",
            "webhook_url": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    # Verify update
    detail = await client.get("/monitors/1")
    assert "Updated Name" in detail.text


@pytest.mark.asyncio
async def test_delete_monitor(client):
    await register_and_get_cookie(client)

    # Create monitor
    await client.post(
        "/monitors/new",
        data={
            "name": "To Delete",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )

    # Delete
    response = await client.post("/monitors/1/delete", follow_redirects=False)
    assert response.status_code == 303

    # Verify gone
    dashboard = await client.get("/dashboard")
    assert "To Delete" not in dashboard.text


@pytest.mark.asyncio
async def test_pause_resume_monitor(client):
    await register_and_get_cookie(client)

    # Create monitor
    await client.post(
        "/monitors/new",
        data={
            "name": "Pausable",
            "period": "3600",
            "grace": "0",
            "webhook_url": "",
        },
        follow_redirects=False,
    )

    # Pause
    response = await client.post("/monitors/1/pause", follow_redirects=False)
    assert response.status_code == 303

    # Check paused
    detail = await client.get("/monitors/1")
    assert "Paused" in detail.text

    # Resume
    response = await client.post("/monitors/1/resume", follow_redirects=False)
    assert response.status_code == 303

    # Check resumed to "new" (no pings yet)
    detail = await client.get("/monitors/1")
    assert "New" in detail.text


@pytest.mark.asyncio
async def test_monitor_not_found_redirects(client):
    await register_and_get_cookie(client)
    response = await client.get("/monitors/999", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_monitor_stats(client):
    await register_and_get_cookie(client)

    # Create a few monitors
    for name in ["Monitor A", "Monitor B", "Monitor C"]:
        await client.post(
            "/monitors/new",
            data={
                "name": name,
                "period": "3600",
                "grace": "0",
                "webhook_url": "",
            },
            follow_redirects=False,
        )

    dashboard = await client.get("/dashboard")
    assert response_contains_stat(dashboard.text, "3")  # Total count


def response_contains_stat(text: str, value: str) -> bool:
    """Check if a stat value appears in the dashboard."""
    return value in text
