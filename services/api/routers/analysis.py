from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.analysis.contract import ContractIntelligence
from services.api.auth.dependencies import TenantContext, get_tenant_context
from services.api.database import get_db

router = APIRouter(prefix="/analysis", tags=["Contract & Document Analysis"])


class SummarizeRequest(BaseModel):
    document_id: str


class ExtractClausesRequest(BaseModel):
    document_id: str


class ExtractObligationsRequest(BaseModel):
    document_id: str


class CompareContractsRequest(BaseModel):
    document_a_id: str
    document_b_id: str


@router.post("/summarize")
async def summarize(
    req: SummarizeRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ContractIntelligence.summarize_document(req.document_id, tenant.workspace_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": str(e)})


@router.post("/extract-clauses")
async def extract_clauses(
    req: ExtractClausesRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    clauses = await ContractIntelligence.extract_clauses(req.document_id, tenant.workspace_id, db)
    return {"document_id": req.document_id, "clauses": clauses}


@router.post("/extract-obligations")
async def extract_obligations(
    req: ExtractObligationsRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    obligations = await ContractIntelligence.extract_obligations(req.document_id, tenant.workspace_id, db)
    return {"document_id": req.document_id, "obligations": obligations}


@router.post("/compare")
async def compare_contracts(
    req: CompareContractsRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ContractIntelligence.compare_contracts(req.document_a_id, req.document_b_id, tenant.workspace_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error_code": "COMPARISON_FAILED", "message": str(e)})


class RemediateClauseRequest(BaseModel):
    clause_type: str
    original_text: str
    risk_level: Optional[str] = "HIGH"
    negotiation_stance: Optional[str] = "BALANCED"


@router.post("/remediate-clause")
async def remediate_clause(
    req: RemediateClauseRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    return ContractIntelligence.remediate_clause(
        clause_type=req.clause_type,
        original_text=req.original_text,
        risk_level=req.risk_level or "HIGH",
        negotiation_stance=req.negotiation_stance or "BALANCED",
    )
