import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient):
    import uuid
    uid_a = str(uuid.uuid4())[:8]
    uid_b = str(uuid.uuid4())[:8]

    # 1. Register User in Workspace A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"usera{uid_a}@firma.com",
            "password": "Password123!",
            "full_name": "Counsel A",
            "workspace_name": f"Workspace Alpha {uid_a}",
        },
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Upload Confidential Document in Workspace A
    doc_text = "CONFIDENTIAL PATENT SETTLEMENT IN WORKSPACE A."
    files = {"file": ("secret_settlement.txt", doc_text.encode("utf-8"), "text/plain")}
    up_a = await client.post("/api/v1/documents", headers=headers_a, files=files, data={"title": "Secret Settlement"})
    doc_a_id = up_a.json()["id"]

    # 2. Register User in Workspace B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"userb{uid_b}@firmb.com",
            "password": "Password123!",
            "full_name": "Counsel B",
            "workspace_name": f"Workspace Beta {uid_b}",
        },
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B attempts to access Document A -> Must return 404 Not Found
    get_res = await client.get(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # 4. User B attempts to get status of Document A -> Must return 404
    status_res = await client.get(f"/api/v1/documents/{doc_a_id}/status", headers=headers_b)
    assert status_res.status_code == 404

    # 5. User B searches for content of Document A -> Must return 0 hits and ABSTAIN
    search_res = await client.post(
        "/api/v1/research",
        headers=headers_b,
        json={"query": "What are the terms of the secret settlement?"},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["status"] == "ABSTAINED"
    assert len(search_data["citations"]) == 0
