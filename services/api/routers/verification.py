from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth.dependencies import TenantContext, get_tenant_context
from services.api.database import get_db
from services.api.trust.verifier import TrustEngine, TrustVerificationSummary

router = APIRouter(prefix="/verification", tags=["Trust & Verification"])


class VerificationCheckRequest(BaseModel):
    citations: list[dict[str, Any]]
    claims: list[dict[str, Any]]


@router.post("/check", response_model=TrustVerificationSummary)
async def verify_output(
    req: VerificationCheckRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await TrustEngine.verify_citations_and_claims(
        citations=req.citations,
        claims=req.claims,
        workspace_id=tenant.workspace_id,
        db=db,
    )
