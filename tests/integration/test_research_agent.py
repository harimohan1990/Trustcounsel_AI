import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_legal_research_agent_workflow(client: AsyncClient):
    # 1. Register & upload contract
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "researcher_test@firm.com",
            "password": "Password123!",
            "full_name": "Senior Legal Researcher",
            "workspace_name": "Corporate Vault",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    contract_text = (
        "SECTION 14. LIMITATION OF LIABILITY\n"
        "In no event shall either party's aggregate liability under this agreement exceed the total fees paid in the past 12 months.\n\n"
        "SECTION 15. CONFIDENTIALITY\n"
        "Confidentiality obligations remain binding for two (2) years following termination.\n"
    )
    files = {"file": ("msa_terms.txt", contract_text.encode("utf-8"), "text/plain")}
    up = await client.post("/api/v1/documents", headers=headers, files=files, data={"title": "MSA Terms"})
    assert up.status_code == 202

    # 2. Execute research query
    res = await client.post(
        "/api/v1/research",
        headers=headers,
        json={"query": "What is the liability cap under the agreement?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] is not None
    assert len(data["answer"]) > 0
    assert len(data["citations"]) >= 1
    assert len(data["claims"]) >= 1

    # Verify citation fields
    cit = data["citations"][0]
    assert cit["chunk_id"] is not None
    assert cit["document_name"] in ["msa_terms.txt", "MSA Terms"]
    assert cit["quote_snippet"] is not None

    # 3. Check research run details endpoint
    run_id = data["run_id"]
    run_detail = await client.get(f"/api/v1/research/{run_id}", headers=headers)
    assert run_detail.status_code == 200
    assert run_detail.json()["query"] == "What is the liability cap under the agreement?"
