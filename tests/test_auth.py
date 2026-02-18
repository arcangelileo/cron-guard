import pytest
from app.auth import hash_password, verify_password, create_access_token, decode_access_token


@pytest.mark.asyncio
async def test_register_page(client):
    response = await client.get("/auth/register")
    assert response.status_code == 200
    assert "Create your account" in response.text


@pytest.mark.asyncio
async def test_login_page(client):
    response = await client.get("/auth/login")
    assert response.status_code == 200
    assert "Welcome back" in response.text


@pytest.mark.asyncio
async def test_register_success(client):
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
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_short_username(client):
    response = await client.post(
        "/auth/register",
        data={
            "username": "ab",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
    )
    assert response.status_code == 422
    assert "at least 3 characters" in response.text


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "not-an-email",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
    )
    assert response.status_code == 422
    assert "valid email" in response.text


@pytest.mark.asyncio
async def test_register_password_mismatch(client):
    response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "differentpassword",
        },
    )
    assert response.status_code == 422
    assert "do not match" in response.text


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
            "password_confirm": "short",
        },
    )
    assert response.status_code == 422
    assert "at least 8 characters" in response.text


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    # Register first user
    await client.post(
        "/auth/register",
        data={
            "username": "user1",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )

    # Register second user with same email
    response = await client.post(
        "/auth/register",
        data={
            "username": "user2",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
    )
    assert response.status_code == 422
    assert "already exists" in response.text


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    # Register first user
    await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "user1@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )

    # Register second user with same username
    response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "user2@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
    )
    assert response.status_code == 422
    assert "already taken" in response.text


@pytest.mark.asyncio
async def test_login_success(client):
    # Register first
    await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )

    # Logout
    await client.get("/auth/logout", follow_redirects=False)

    # Login
    response = await client.post(
        "/auth/login",
        data={
            "email": "test@example.com",
            "password": "securepassword123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    # Register first
    await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )

    # Login with wrong password
    response = await client.post(
        "/auth/login",
        data={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    response = await client.post(
        "/auth/login",
        data={
            "email": "nobody@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


@pytest.mark.asyncio
async def test_logout(client):
    # Register
    await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )

    response = await client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"


def test_hash_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_and_decode_token():
    token = create_access_token({"sub": "42"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"


def test_decode_invalid_token():
    payload = decode_access_token("invalid.token.here")
    assert payload is None


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client):
    response = await client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_settings_requires_auth_redirect(client):
    """Settings page should redirect unauthenticated users to login."""
    response = await client.get("/settings", follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_monitors_new_requires_auth(client):
    """New monitor page should redirect unauthenticated users to login."""
    response = await client.get("/monitors/new", follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_authenticated_user_redirected_from_login(client):
    # Register (auto-login)
    reg_response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    # Set cookie for subsequent requests
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))

    # Try to visit login page — should redirect to dashboard
    response = await client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_authenticated_user_redirected_from_register(client):
    """Authenticated user visiting register page should redirect to dashboard."""
    reg_response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))

    response = await client.get("/auth/register", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_expired_token_redirects_to_login(client):
    """An invalid/expired token should redirect to login."""
    client.cookies.set("access_token", "invalid-token-here")
    response = await client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_root_redirects(client):
    """Root URL should redirect to login when not authenticated."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_root_redirects_to_dashboard_when_authed(client):
    """Root URL should redirect to dashboard when authenticated."""
    reg_response = await client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))

    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert "/dashboard" in response.headers["location"]
