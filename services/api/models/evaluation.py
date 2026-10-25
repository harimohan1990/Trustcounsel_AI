import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.api.database import Base


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    cases = relationship("EvaluationCase", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_chunk_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    should_abstain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    dataset = relationship("EvaluationDataset", back_populates="cases")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    model_identifier: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    
    # Metrics
    recall_at_k: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    precision_at_k: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mrr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ndcg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    faithfulness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    citation_precision: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    abstention_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p95_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    dataset = relationship("EvaluationDataset", back_populates="runs")
