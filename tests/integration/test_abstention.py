import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_automated_abstention_on_unanswerable_query(client: AsyncClient):
    # 1. Register empty workspace
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "abstain_user@firm.com",
            "password": "Password123!",
            "full_name": "Risk Officer",
            "workspace_name": "Empty Space",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Query with zero documents in workspace -> must ABSTAIN
    res = await client.post(
        "/api/v1/research",
        headers=headers,
        json={"query": "What is the penalty for maritime vessel collision under admiralty law?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ABSTAINED"
    assert data["confidence_score"] == 0.0
    assert "INSUFFICIENT EVIDENCE" in data["answer"]
    assert len(data["citations"]) == 0
