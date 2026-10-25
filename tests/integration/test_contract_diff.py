import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_contract_intelligence_and_comparison(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "diff_analyst@firm.com",
            "password": "Password123!",
            "full_name": "Diff Analyst",
            "workspace_name": "M&A Vault",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Version A
    doc_a_text = "Standard NDA. Section 1. Confidentiality. Term is 2 years. Governing law is Delaware. Liability capped at 1x fees."
    files_a = {"file": ("NDA_v1.txt", doc_a_text.encode("utf-8"), "text/plain")}
    res_a = await client.post("/api/v1/documents", headers=headers, files=files_a, data={"title": "NDA v1"})
    doc_a_id = res_a.json()["id"]

    # Upload Version B (modified)
    doc_b_text = "Modified NDA. Section 1. Confidentiality. Term is 5 years. Governing law is New York. Liability capped at 3x fees."
    files_b = {"file": ("NDA_v2.txt", doc_b_text.encode("utf-8"), "text/plain")}
    res_b = await client.post("/api/v1/documents", headers=headers, files=files_b, data={"title": "NDA v2"})
    doc_b_id = res_b.json()["id"]

    # 1. Summarize Doc A
    sum_res = await client.post("/api/v1/analysis/summarize", headers=headers, json={"document_id": doc_a_id})
    assert sum_res.status_code == 200
    assert "summary" in sum_res.json()

    # 2. Extract clauses from Doc A
    clause_res = await client.post("/api/v1/analysis/extract-clauses", headers=headers, json={"document_id": doc_a_id})
    assert clause_res.status_code == 200
    assert len(clause_res.json()["clauses"]) > 0

    # 3. Compare Version A vs Version B
    diff_res = await client.post(
        "/api/v1/analysis/compare",
        headers=headers,
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id},
    )
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert "modified_clauses" in diff_data
    assert len(diff_data["modified_clauses"]) >= 1

    # Verify high materiality flag
    high_risk = next((c for c in diff_data["modified_clauses"] if c["materiality"] == "HIGH"), None)
    assert high_risk is not None
    assert "liability" in high_risk["clause_type"].lower()

    # 4. Remediate High-Risk Clause
    rem_res = await client.post(
        "/api/v1/analysis/remediate-clause",
        headers=headers,
        json={
            "clause_type": "Limitation of Liability",
            "original_text": high_risk["text_b"],
            "risk_level": "HIGH",
            "negotiation_stance": "BALANCED",
        },
    )
    assert rem_res.status_code == 200
    rem_data = rem_res.json()
    assert "proposed_redline" in rem_data
    assert "fallback_option" in rem_data
    assert "negotiation_rationale" in rem_data
    assert "playbook_rule" in rem_data
    assert "Section 4.1 Limitation of Liability" in rem_data["proposed_redline"]
