from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth.dependencies import TenantContext, require_role
from services.api.database import get_db
from services.api.models.audit import AuditEvent
from services.api.models.research import (
    Claim,
    EvidenceReference,
    ResearchRun,
    RunStatus,
)
from services.api.models.review import ReviewDecision, ReviewStatus, ReviewTask
from services.api.models.user import UserRole

router = APIRouter(prefix="/reviews", tags=["Human Review Queue"])


class ReviewDecisionRequest(BaseModel):
    decision: ReviewStatus
    notes: str
    modified_answer: str | None = None


@router.get("")
async def list_review_tasks(
    status: ReviewStatus | None = None,
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ReviewTask, ResearchRun.query)
        .join(ResearchRun, ReviewTask.run_id == ResearchRun.id)
        .where(ReviewTask.workspace_id == tenant.workspace_id)
    )
    if status:
        stmt = stmt.where(ReviewTask.status == status)

    stmt = stmt.order_by(ReviewTask.created_at.desc())
    res = await db.execute(stmt)
    rows = res.all()

    return {
        "tasks": [
            {
                "id": t.id,
                "run_id": t.run_id,
                "query": query,
                "trigger_reason": t.trigger_reason,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
            }
            for t, query in rows
        ]
    }


@router.get("/{review_id}")
async def get_review_task(
    review_id: str,
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ReviewTask).where(ReviewTask.id == review_id, ReviewTask.workspace_id == tenant.workspace_id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Review task not found"})

    run_res = await db.execute(select(ResearchRun).where(ResearchRun.id == task.run_id))
    run = run_res.scalar_one_or_none()

    ev_res = await db.execute(select(EvidenceReference).where(EvidenceReference.run_id == task.run_id))
    citations = ev_res.scalars().all()

    cl_res = await db.execute(select(Claim).where(Claim.run_id == task.run_id))
    claims = cl_res.scalars().all()

    return {
        "id": task.id,
        "run_id": task.run_id,
        "query": run.query if run else "",
        "trigger_reason": task.trigger_reason,
        "status": task.status.value,
        "draft_answer": run.raw_answer if run else "",
        "confidence_score": run.confidence_score if run else 0.0,
        "citations": [
            {
                "id": c.id,
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_name": c.document_name,
                "page_number": c.page_number,
                "quote_snippet": c.quote_snippet,
                "verified": c.is_quote_verified,
            }
            for c in citations
        ],
        "claims": [
            {
                "id": cl.id,
                "claim_text": cl.claim_text,
                "status": cl.status.value,
            }
            for cl in claims
        ],
    }


@router.post("/{review_id}/decision")
async def submit_decision(
    review_id: str,
    req: ReviewDecisionRequest,
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ReviewTask).where(ReviewTask.id == review_id, ReviewTask.workspace_id == tenant.workspace_id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Review task not found"})

    # Create immutable decision record
    decision = ReviewDecision(
        review_task_id=task.id,
        reviewer_id=tenant.user_id,
        decision=req.decision,
        reviewer_notes=req.notes,
        modified_answer=req.modified_answer,
    )
    db.add(decision)

    # Update task status
    task.status = req.decision

    # Update corresponding ResearchRun
    run_res = await db.execute(select(ResearchRun).where(ResearchRun.id == task.run_id))
    run = run_res.scalar_one_or_none()
    if run:
        if req.decision == ReviewStatus.APPROVED:
            run.status = RunStatus.COMPLETED
            if req.modified_answer:
                run.verified_answer = req.modified_answer
        elif req.decision == ReviewStatus.REJECTED:
            run.status = RunStatus.ABSTAINED
            run.error_message = f"Rejected by reviewer: {req.notes}"

    # Audit event
    audit = AuditEvent(
        workspace_id=tenant.workspace_id,
        user_id=tenant.user_id,
        action="REVIEW_DECISION_RECORDED",
        entity_type="review_task",
        entity_id=task.id,
        details=f'{{"decision": "{req.decision.value}", "reviewer": "{tenant.full_name}"}}',
    )
    db.add(audit)

    await db.commit()
    return {"success": True, "message": f"Review marked as {req.decision.value}"}
