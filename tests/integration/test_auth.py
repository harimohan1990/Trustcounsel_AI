import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_workflow(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "email": "attorney@lexfirm.com",
        "password": "SecurePassword123!",
        "full_name": "Sarah Jenkins",
        "workspace_name": "LexFirm Legal Matters",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "attorney@lexfirm.com"
    token = data["access_token"]
    workspace_id = data["user"]["workspace_id"]
    assert workspace_id is not None

    # 2. Duplicate registration rejected
    dup_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 409

    # 3. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "attorney@lexfirm.com", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Invalid Login
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "attorney@lexfirm.com", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 5. Get /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "attorney@lexfirm.com"
