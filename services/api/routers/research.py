import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.agent.state import ResearchAgentState
from services.api.agent.workflow import ResearchWorkflowEngine
from services.api.auth.dependencies import TenantContext, get_tenant_context
from services.api.database import get_db
from services.api.models.research import (
    Claim,
    EvidenceReference,
    MessageRole,
    ResearchMessage,
    ResearchRun,
    ResearchSession,
    RunStatus,
)

router = APIRouter(prefix="/research", tags=["Legal Research"])


class ResearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    session_id: str | None = None
    document_ids: list[str] | None = None


class ClaimDto(BaseModel):
    id: str
    claim_text: str
    status: str
    citation_ids: list[str]


class CitationDto(BaseModel):
    id: str
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    quote_snippet: str
    verified: bool


class ResearchResponse(BaseModel):
    run_id: str
    session_id: str | None
    answer: str
    claims: list[ClaimDto]
    citations: list[CitationDto]
    limitations: list[str]
    confidence_score: float
    status: str
    requires_review: bool


@router.post("", response_model=ResearchResponse)
async def execute_research(
    req: ResearchRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    start_time = time.time()
    run_id = str(uuid.uuid4())

    # Get or create session
    session_id = req.session_id
    if not session_id:
        session = ResearchSession(
            workspace_id=tenant.workspace_id,
            user_id=tenant.user_id,
            title=req.query[:60],
        )
        db.add(session)
        await db.flush()
        session_id = session.id

    # Add user message
    user_msg = ResearchMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=req.query,
    )
    db.add(user_msg)
    await db.flush()

    # Initialize workflow state
    state = ResearchAgentState(
        run_id=run_id,
        workspace_id=tenant.workspace_id,
        user_id=tenant.user_id,
        query=req.query,
        document_filter_ids=req.document_ids,
    )

    # Execute LangGraph research agent
    final_state = await ResearchWorkflowEngine.run(state, db)

    total_latency = round((time.time() - start_time) * 1000, 2)

    # Persist ResearchRun record
    status_mapping = {
        "COMPLETED": RunStatus.COMPLETED,
        "ABSTAINED": RunStatus.ABSTAINED,
        "AWAITING_HUMAN_REVIEW": RunStatus.AWAITING_HUMAN_REVIEW,
        "FAILED": RunStatus.FAILED,
    }
    run_status = status_mapping.get(final_state.status, RunStatus.COMPLETED)

    run = ResearchRun(
        id=run_id,
        session_id=session_id,
        workspace_id=tenant.workspace_id,
        user_id=tenant.user_id,
        query=req.query,
        status=run_status,
        raw_answer=final_state.draft_answer,
        verified_answer=final_state.draft_answer,
        confidence_score=final_state.verification_score,
        total_latency_ms=total_latency,
        prompt_tokens=final_state.prompt_tokens,
        completion_tokens=final_state.completion_tokens,
        estimated_cost_usd=final_state.estimated_cost_usd,
    )
    db.add(run)

    # Persist evidence references
    for cit in final_state.citations:
        ev = EvidenceReference(
            run_id=run_id,
            chunk_id=cit.chunk_id,
            document_id=cit.document_id,
            document_name=cit.document_name,
            page_number=cit.page_number,
            quote_snippet=cit.quote_snippet,
            is_quote_verified=cit.is_quote_verified,
        )
        db.add(ev)

    # Persist claims
    for cl in final_state.claims:
        claim_rec = Claim(
            run_id=run_id,
            claim_text=cl.text,
            status=cl.status,
            citation_ids=",".join(cl.supporting_chunk_ids),
        )
        db.add(claim_rec)

    # Add assistant response message to session
    asst_msg = ResearchMessage(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=final_state.draft_answer or "",
    )
    db.add(asst_msg)

    await db.commit()

    return ResearchResponse(
        run_id=run_id,
        session_id=session_id,
        answer=final_state.draft_answer or "",
        claims=[
            ClaimDto(
                id=c.id,
                claim_text=c.text,
                status=c.status,
                citation_ids=c.supporting_chunk_ids,
            )
            for c in final_state.claims
        ],
        citations=[
            CitationDto(
                id=c.id,
                document_id=c.document_id,
                document_name=c.document_name,
                page_number=c.page_number,
                chunk_id=c.chunk_id,
                quote_snippet=c.quote_snippet,
                verified=c.is_quote_verified,
            )
            for c in final_state.citations
        ],
        limitations=final_state.limitations,
        confidence_score=final_state.verification_score,
        status=final_state.status,
        requires_review=(final_state.status == "AWAITING_HUMAN_REVIEW"),
    )


@router.get("/sessions")
async def list_sessions(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ResearchSession)
        .where(ResearchSession.workspace_id == tenant.workspace_id)
        .order_by(ResearchSession.updated_at.desc())
    )
    sessions = res.scalars().all()
    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.workspace_id == tenant.workspace_id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Session not found"})

    msg_res = await db.execute(
        select(ResearchMessage)
        .where(ResearchMessage.session_id == session_id)
        .order_by(ResearchMessage.created_at.asc())
    )
    messages = msg_res.scalars().all()

    return {
        "id": session.id,
        "title": session.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.get("/{run_id}")
async def get_research_run(
    run_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ResearchRun).where(
            ResearchRun.id == run_id,
            ResearchRun.workspace_id == tenant.workspace_id,
        )
    )
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Research run not found"})

    ev_res = await db.execute(select(EvidenceReference).where(EvidenceReference.run_id == run_id))
    citations = ev_res.scalars().all()

    cl_res = await db.execute(select(Claim).where(Claim.run_id == run_id))
    claims = cl_res.scalars().all()

    return {
        "run_id": run.id,
        "query": run.query,
        "status": run.status.value,
        "answer": run.verified_answer or run.raw_answer,
        "confidence_score": run.confidence_score,
        "total_latency_ms": run.total_latency_ms,
        "tokens": {
            "prompt": run.prompt_tokens,
            "completion": run.completion_tokens,
            "total": run.prompt_tokens + run.completion_tokens,
        },
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
