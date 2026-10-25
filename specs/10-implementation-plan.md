# Implementation Plan: TrustCounsel AI
**Document ID:** SPEC-10-PLAN  
**Version:** 1.0.0  
**Phase:** 5 — Implementation Plan  
**Status:** Approved & Baselined  

---

## 1. Development Methodology & Phasing Rules

TrustCounsel AI adheres strictly to **Specification-Driven Development (SDD)**:
1. Every milestone implements an isolated, testable, and demonstrable vertical slice.
2. Code is written against approved schemas and contracts.
3. Every milestone must pass all linting, type checks, and automated tests before proceeding to the next.
4. No fake completion claims or mock values presented as live database data.

---

## 2. Implementation Milestones

### Milestone 1 — SDD Foundation & Contracts [COMPLETED]
- **Requirements Covered:** Discovery, PRD, Architecture, Data Models, OpenAPI Contracts, Threat Model, Test Specs, Traceability.
- **Deliverables:** `specs/00` through `specs/10`, `specs/traceability.md`, `specs/adr/*`.
- **Exit Criteria:** All specifications baselined and committed to Git.

---

### Milestone 2 — Application & Infrastructure Foundation
- **Requirements Covered:** `FR-001` to `FR-006`, `NFR-001`, `NFR-005`, `NFR-006`.
- **Scope:**
  - Monorepo directory structure (`apps/web`, `services/api`, `packages/shared-contracts`, `tests`, `docker-compose.yml`, `Makefile`).
  - FastAPI 0.115+ backend with SQLAlchemy 2.0 async engine and Alembic migrations.
  - PostgreSQL 16 + pgvector container configuration.
  - User registration, password hashing (bcrypt), JWT generation, tenant context middleware.
  - React 19 + TypeScript + Vite + Tailwind CSS shell with authentication views.
  - Health (`/health`, `/ready`) endpoints and baseline test harness.
- **Tests to Execute:** `tests/integration/test_auth.py`, `tests/security/test_tenant_isolation.py`.
- **Rollback Strategy:** Database migration downgrade `alembic downgrade base`.

---

### Milestone 3 — Document Ingestion & Hybrid Retrieval Engine
- **Requirements Covered:** `FR-007` to `FR-014`, `FR-017`, `NFR-002`, `NFR-003`.
- **Scope:**
  - PDF/TXT upload handler with MIME validation and SHA-256 deduplication.
  - Text extraction pipeline preserving page boundaries and line breaks.
  - Text chunking engine (512 token window, 64 token overlap, positional metadata).
  - Pluggable embedding provider abstraction with local `MockEmbeddingProvider` (384-d).
  - pgvector + PostgreSQL full-text search hybrid query with Reciprocal Rank Fusion (RRF).
  - Document status lifecycle management (`UPLOADED -> PROCESSING -> INDEXED / FAILED`).
  - Documents UI tab in React (file upload dropzone, processing progress, document table).
- **Tests to Execute:** `tests/unit/test_chunking.py`, `tests/integration/test_ingestion.py`, `tests/integration/test_retrieval.py`.

---

### Milestone 4 — Legal Research Agent (LangGraph)
- **Requirements Covered:** `FR-015`, `FR-016`, `FR-018`, `FR-019`, `FR-020`, `NFR-010`.
- **Scope:**
  - Typed LangGraph research graph implementation (`validate_request`, `plan_research`, `retrieve_evidence`, `rerank_evidence`, `analyze_documents`, `draft_response`, `finalize_response`).
  - Pluggable LLM provider abstraction with deterministic `MockLLMProvider` for local testing.
  - Structured output synthesis conforming to `ResearchResponse` schema.
  - Persistent research session management (`research_sessions`, `research_messages`, `research_runs`).
  - Three-panel Research Workspace in React (left: sessions; center: query & answer; right: source document preview).
- **Tests to Execute:** `tests/integration/test_research_agent.py`, `tests/integration/test_sessions.py`.

---

### Milestone 5 — Trust & Verification Engine
- **Requirements Covered:** `FR-026` to `FR-032`, `US-1`, `US-3`.
- **Scope:**
  - Deterministic Citation Entity Resolution (verifying chunk presence in tenant workspace).
  - Quote Grounding Validator (Levenshtein similarity >= 0.95 against source chunk).
  - Claim-level evidence coverage scoring and unsupported claim flagging (`UNSUPPORTED`).
  - Contradiction detector across competing passages.
  - Automated Abstention logic (`INSUFFICIENT_EVIDENCE`) when similarity is low.
  - Automated Human Review routing trigger when confidence < 0.85 or conflicts exist.
  - Interactive Citation Inspector UI in React (click citation to scroll & highlight passage).
- **Tests to Execute:** `tests/unit/test_verification.py`, `tests/integration/test_abstention.py`.

---

### Milestone 6 — Contract & Document Intelligence
- **Requirements Covered:** `FR-021` to `FR-025`, `US-2`.
- **Scope:**
  - Structured executive summary generator with citations.
  - 9-category clause extractor (Indemnification, Governing Law, Liability Caps, Termination, etc.).
  - Obligation extraction engine (party, action, deadline, citation).
  - Side-by-side contract comparison redline engine (Added, Removed, Modified clauses).
  - Risk indicator generator with materiality levels (`LOW`, `MEDIUM`, `HIGH`) and rationale.
  - Contract Intelligence & Redline Diff UI in React.
- **Tests to Execute:** `tests/unit/test_analysis.py`, `tests/integration/test_contract_diff.py`.

---

### Milestone 7 — Human Review Queue & Evaluation Engine
- **Requirements Covered:** `FR-033` to `FR-040`, `US-3`.
- **Scope:**
  - Priority Human Review queue endpoints (`/reviews`, `/reviews/{id}/decision`).
  - Reviewer decision recording (`APPROVED`, `REJECTED`, `REVISION_REQUESTED`) with audit notes.
  - Evaluation dataset management and automated benchmark runner (`/evaluations/runs`).
  - Metric calculators (Recall@K, MRR, nDCG, Citation Precision, Faithfulness, Abstention Accuracy).
  - Baseline comparison engine reporting regression deltas.
  - Human Review Queue UI and Observability & Evaluation Dashboard UI in React.
- **Tests to Execute:** `tests/integration/test_review_queue.py`, `tests/evaluation/test_eval_metrics.py`.

---

### Milestone 8 — Hardening, Observability & Final Packaging
- **Requirements Covered:** `NFR-001` to `NFR-014`, Acceptance Scenarios 1–17.
- **Scope:**
  - Automated security audit suite (cross-tenant penetration tests, prompt injection tests).
  - Load testing script (`scripts/run_load_test.py`).
  - Structured logging with correlation IDs and OpenTelemetry instrumentation.
  - Full Docker Compose build validation.
  - End-to-end user journey demonstration with synthetic contracts.
  - Comprehensive `README.md` and `Makefile`.
- **Tests to Execute:** Full test suite (`pytest`), linting (`ruff`), and frontend build validation.
