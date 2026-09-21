import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_admin_login(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@hospital.com",
            "password": "Admin@123456",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ADMINISTRATOR"
    assert data["email"] == "admin@hospital.com"

    # Test /auth/me with token
    token = data["access_token"]
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "admin@hospital.com"
    assert me_data["role"]["name"] == "ADMINISTRATOR"


@pytest.mark.asyncio
async def test_invalid_login(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@hospital.com",
            "password": "WrongPassword123",
        },
    )
    assert response.status_code == 401
