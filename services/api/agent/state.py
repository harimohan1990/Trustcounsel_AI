from typing import Literal

from pydantic import BaseModel, Field


class RetrievedChunkItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    similarity_score: float
    rank: int


class AtomicClaimItem(BaseModel):
    id: str
    text: str
    supporting_chunk_ids: list[str] = Field(default_factory=list)
    status: Literal["VERIFIED", "UNSUPPORTED", "CONTRADICTED"] = "VERIFIED"
    verification_notes: str | None = None


class CitationItem(BaseModel):
    id: str
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    quote_snippet: str
    is_quote_verified: bool = False


class AgentStepTraceItem(BaseModel):
    step_name: str
    duration_ms: float
    input_summary: str
    output_summary: str
    status: str = "COMPLETED"


class ResearchAgentState(BaseModel):
    run_id: str
    workspace_id: str
    user_id: str
    query: str
    document_filter_ids: list[str] | None = None

    sub_queries: list[str] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunkItem] = Field(default_factory=list)
    evidence_score: float = 0.0

    draft_answer: str | None = None
    claims: list[AtomicClaimItem] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    verification_score: float = 0.0
    status: Literal["RUNNING", "COMPLETED", "ABSTAINED", "AWAITING_HUMAN_REVIEW", "FAILED"] = "RUNNING"
    abstention_reason: str | None = None
    human_review_task_id: str | None = None

    traces: list[AgentStepTraceItem] = Field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
