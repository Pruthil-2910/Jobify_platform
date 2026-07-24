import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "fullname": "John Doe",
        "email": "johndoe@example.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert data["fullname"] == "John Doe"
    assert data["email"] == "johndoe@example.com"
    assert "hashed_password" not in data  # Ensure sensitive hash is not exposed


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """Test registering with an email that is already registered fails with 400."""
    payload = {
        "fullname": "Duplicate User",
        "email": test_user.email,
        "password": "AnotherPassword123!",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


@pytest.mark.asyncio
async def test_register_validation_error(client: AsyncClient):
    """Test registering with invalid email or missing fields fails with 422."""
    payload = {
        "fullname": "Short Password",
        "email": "not-an-email",
        "password": "123",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login returns user payload and sets access_token cookie."""
    payload = {
        "email": test_user.email,
        "password": "TestPassword123!",
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == test_user.email

    # Verify cookie setting
    assert "access_token" in response.cookies
    assert response.cookies["access_token"] is not None


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Test login with incorrect password returns 401 Unauthorized."""
    payload = {
        "email": test_user.email,
        "password": "WrongPassword123!",
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent email returns 401 Unauthorized."""
    payload = {
        "email": "nonexistent@example.com",
        "password": "SomePassword123!",
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout endpoint returns 200 and removes access_token cookie."""
    response = await client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}


@pytest.mark.asyncio
async def test_me_authenticated(authenticated_client: AsyncClient, test_user: User):
    """Test /auth/me with valid authentication cookie returns user info."""
    response = await authenticated_client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["fullname"] == test_user.fullname


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """Test /auth/me without authentication cookie returns 401 Unauthorized."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    """Test /auth/me with invalid JWT token returns 401 Unauthorized."""
    client.cookies.set("access_token", "invalid.jwt.token")
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
