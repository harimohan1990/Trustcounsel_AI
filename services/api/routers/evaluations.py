from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth.dependencies import TenantContext, require_role
from services.api.database import get_db
from services.api.eval.runner import EvaluationRunner
from services.api.models.evaluation import EvaluationRun
from services.api.models.user import UserRole

router = APIRouter(prefix="/evaluations", tags=["Evaluation & Observability"])


class TriggerEvaluationRequest(BaseModel):
    dataset_name: str = "legal_qa_contracts_v1"
    model_identifier: str = "mock-v1"
    is_baseline: bool = False


@router.get("/runs")
async def list_runs(
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(EvaluationRun)
        .where(EvaluationRun.workspace_id == tenant.workspace_id)
        .order_by(EvaluationRun.created_at.desc())
    )
    runs = res.scalars().all()
    return {
        "runs": [
            {
                "run_id": r.id,
                "model_identifier": r.model_identifier,
                "recall_at_k": r.recall_at_k,
                "precision_at_k": r.precision_at_k,
                "mrr": r.mrr,
                "ndcg": r.ndcg,
                "faithfulness_score": r.faithfulness_score,
                "citation_precision": r.citation_precision,
                "abstention_accuracy": r.abstention_accuracy,
                "p95_latency_ms": r.p95_latency_ms,
                "total_tokens": r.total_tokens,
                "is_baseline": r.is_baseline,
                "created_at": r.created_at.isoformat(),
            }
            for r in runs
        ]
    }


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(
    req: TriggerEvaluationRequest,
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    run = await EvaluationRunner.run_benchmark(
        dataset_name=req.dataset_name,
        workspace_id=tenant.workspace_id,
        db=db,
        model_identifier=req.model_identifier,
        is_baseline=req.is_baseline,
    )
    return {
        "run_id": run.id,
        "model_identifier": run.model_identifier,
        "status": run.status,
        "metrics": {
            "recall_at_k": run.recall_at_k,
            "precision_at_k": run.precision_at_k,
            "mrr": run.mrr,
            "ndcg": run.ndcg,
            "faithfulness_score": run.faithfulness_score,
            "citation_precision": run.citation_precision,
            "abstention_accuracy": run.abstention_accuracy,
            "p95_latency_ms": run.p95_latency_ms,
        },
    }


@router.get("/compare")
async def compare_runs(
    baseline_run_id: str,
    target_run_id: str,
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    b_res = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == baseline_run_id, EvaluationRun.workspace_id == tenant.workspace_id)
    )
    baseline = b_res.scalar_one_or_none()
    t_res = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == target_run_id, EvaluationRun.workspace_id == tenant.workspace_id)
    )
    target = t_res.scalar_one_or_none()

    if not baseline or not target:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Baseline or target evaluation run not found"})

    return EvaluationRunner.compare_runs(baseline, target)
