import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_ingestion_lifecycle(client: AsyncClient):
    # 1. Register user
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ingest_user@firm.com",
            "password": "Password123!",
            "full_name": "Ingestion Analyst",
            "workspace_name": "Ingestion Vault",
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload valid contract TXT
    contract_content = (
        "CONFIDENTIALITY AND MASTER SERVICES AGREEMENT\n\n"
        "1. Parties. This Agreement is made between Alpha Corp and Beta LLC.\n"
        "2. Limitation of Liability. The total aggregate liability shall not exceed $500,000.\n"
        "3. Governing Law. This Agreement is governed by Delaware law.\n"
    )
    files = {"file": ("test_agreement.txt", contract_content.encode("utf-8"), "text/plain")}
    data = {"title": "Master Services Agreement", "classification": "MSA"}

    upload_res = await client.post("/api/v1/documents", headers=headers, files=files, data=data)
    assert upload_res.status_code == 202
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "INDEXED"
    assert doc_data["content_hash"] is not None

    # 3. Check status
    status_res = await client.get(f"/api/v1/documents/{doc_id}/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "INDEXED"
    assert status_res.json()["chunk_count"] >= 1

    # 4. List documents
    list_res = await client.get("/api/v1/documents", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 5. Reject invalid file type
    bad_files = {"file": ("payload.exe", b"\x00\x01\x02", "application/octet-stream")}
    bad_res = await client.post("/api/v1/documents", headers=headers, files=bad_files)
    assert bad_res.status_code == 400
