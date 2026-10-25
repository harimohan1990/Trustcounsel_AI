# Acceptance Test Specifications: TrustCounsel AI
**Document ID:** SPEC-07-TEST  
**Version:** 1.0.0  
**Phase:** 4 — Test Specifications  
**Status:** Approved & Baselined  

---

## 1. Overview & Test Harness Architecture

The test suite is structured into clear tiers with deterministic fixtures:
- **Unit Tests (`tests/unit/`):** Fast, in-memory validation of text chunking, token estimation, Levenshtein quote matching, RRF score fusion, and Pydantic schema validation. Zero network or DB dependencies.
- **Integration Tests (`tests/integration/`):** FastAPI `TestClient` tests with test database (PostgreSQL + pgvector or SQLite with vector fallback for lightweight CI), testing end-to-end API workflows, database persistence, and LangGraph agent runs.
- **Security Tests (`tests/security/`):** Cross-tenant data isolation attacks, prompt injection fuzzing, expired JWT token rejection, and RBAC authorization boundary testing.
- **Evaluation Tests (`tests/evaluation/`):** Golden test dataset runs asserting retrieval metrics (Recall@K, MRR) and verification benchmarks.

---

## 2. Core Acceptance Scenarios (Traceable to PRD)

### Scenario 1: User Registration & Workspace Isolation (`FR-001`, `FR-003`, `US-1`)
- **Test File:** `tests/integration/test_auth.py`
- **Given:** A new user with email `counsel@firm.com`, password `Password123!`, and workspace `Apex Legal`.
- **When:** `POST /api/v1/auth/register` is invoked.
- **Then:**
  - Status is HTTP 201.
  - User is assigned role `RESEARCHER`.
  - A workspace with slug `apex-legal` is created.
  - Returned JWT contains `workspace_id`.

### Scenario 2: Valid Document Ingestion & Status Tracking (`FR-007`, `FR-012`, `NFR-003`)
- **Test File:** `tests/integration/test_ingestion.py`
- **Given:** A valid 5-page sample contract PDF (`fixtures/sample_nda.pdf`).
- **When:** `POST /api/v1/documents` is invoked with valid bearer token.
- **Then:**
  - Status is HTTP 202 with `status: "UPLOADED"`.
  - Background worker extracts text and chunks document.
  - Subsequent `GET /api/v1/documents/{id}/status` transitions from `PROCESSING` to `INDEXED`.
  - `document_chunks` table contains >= 5 chunks with embeddings and TSVectors.

### Scenario 3: Invalid File Type Rejection (`FR-007`, `NFR-008`)
- **Test File:** `tests/integration/test_ingestion.py`
- **Given:** An unsupported file `malicious.exe` or `data.bin`.
- **When:** `POST /api/v1/documents` is invoked.
- **Then:**
  - Status is HTTP 400 Bad Request with `INVALID_FILE_TYPE`.
  - No database records or filesystem files are created.

### Scenario 4: Hybrid Search Retrieval (`FR-017`, `NFR-002`)
- **Test File:** `tests/integration/test_retrieval.py`
- **Given:** An indexed contract containing "The liability cap shall not exceed $1,000,000".
- **When:** Querying hybrid search with "What is the limitation of liability?".
- **Then:**
  - The chunk containing "$1,000,000" is returned in Top 3 candidates.
  - Both pgvector cosine similarity and FTS tsvector contribute to the RRF score.

### Scenario 5: Legal Research Answer with Verified Citations (`FR-015`, `FR-018`, `FR-026`)
- **Test File:** `tests/integration/test_research_agent.py`
- **Given:** An indexed NDA with a 2-year non-disclosure obligation.
- **When:** `POST /api/v1/research` query "What is the confidentiality term?".
- **Then:**
  - Returns `ResearchResponse` with status `COMPLETED`.
  - Answer states the 2-year term.
  - At least 1 citation is present linking to the exact `chunk_id` and page number.
  - `is_quote_verified` is `True`.

### Scenario 6: Unsupported Claims & Automated Abstention (`FR-029`, `FR-031`)
- **Test File:** `tests/integration/test_abstention.py`
- **Given:** Workspace with documents solely regarding software licensing.
- **When:** Querying "What is the penalty for maritime vessel collision?".
- **Then:**
  - Agent determines retrieved chunks have similarity score < 0.60.
  - Returns status `ABSTAINED` with `confidence_score: 0.0`.
  - Explanation explicitly states evidence is insufficient.
  - Zero hallucinated citations are generated.

### Scenario 7: Contradictory Evidence Surfacing (`FR-030`)
- **Test File:** `tests/integration/test_verification.py`
- **Given:** Document A specifying "Delaware law governs" and Document B amendment specifying "New York law governs".
- **When:** Querying "What is the governing law of the agreement?".
- **Then:**
  - The response identifies the conflicting governing law clauses.
  - Cites both documents.
  - Automatically routes to `AWAITING_HUMAN_REVIEW`.

### Scenario 8: Clause Extraction & Contract Summary (`FR-021`, `FR-022`)
- **Test File:** `tests/integration/test_analysis.py`
- **Given:** An indexed Master Services Agreement.
- **When:** `POST /api/v1/analysis/extract-clauses` is invoked.
- **Then:**
  - Structured clauses returned across standard categories (Indemnification, Governing Law, Termination).
  - Each extracted clause links to page number and snippet.

### Scenario 9: Contract Redline Comparison (`FR-024`)
- **Test File:** `tests/integration/test_analysis.py`
- **Given:** Document A (standard NDA) and Document B (modified counterparty NDA).
- **When:** `POST /api/v1/analysis/compare` is executed.
- **Then:**
  - Returns categorized diff: `added_clauses`, `removed_clauses`, `modified_clauses`.
  - Flags modified indemnity clause as `HIGH` materiality risk.

### Scenario 10: Multi-Tenant Cross-Workspace Boundary Defense (`NFR-005`)
- **Test File:** `tests/security/test_tenant_isolation.py`
- **Given:** User 1 in `Workspace A` with Document 1; User 2 in `Workspace B`.
- **When:** User 2 attempts `GET /api/v1/documents/{doc_1_id}` or submits research query targeting Doc 1.
- **Then:**
  - API returns HTTP 404 Not Found.
  - Research retrieval in Workspace B returns 0 chunks from Workspace A.
  - Trust Engine rejects any citation pointing to Doc 1.

### Scenario 11: Workflow Checkpoint Recovery (`NFR-010`)
- **Test File:** `tests/integration/test_research_agent.py`
- **Given:** A research run paused at `AWAITING_HUMAN_REVIEW`.
- **When:** Reviewer approves the task via `POST /api/v1/reviews/{id}/decision`.
- **Then:**
  - LangGraph resumes from checkpoint without re-running retrieval or generation.
  - Final response transitions to `COMPLETED`.

### Scenario 12: Human Review Decision Audit Trail (`FR-035`, `FR-036`)
- **Test File:** `tests/integration/test_review_queue.py`
- **Given:** A pending review task.
- **When:** Reviewer submits `APPROVED` with notes "Verified against master agreement".
- **Then:**
  - `review_decisions` stores record with `reviewer_id`, timestamp, notes.
  - `audit_events` records `REVIEW_APPROVED` event.
