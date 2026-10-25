# Discovery Report: TrustCounsel AI
**Phase 0 — Repository and Environment Discovery**
**Date:** 2026-10-25
**Status:** Approved & Baselined

---

## 1. Executive Summary

TrustCounsel AI is an enterprise-grade legal research and document intelligence platform designed to deliver verified, citation-backed answers, contract intelligence, claim-level truth verification, and stateful human-in-the-loop workflows. 

This discovery audit establishes the baseline environment, available tooling, repository structure, core dependencies, and technical assumptions before writing architecture or code.

---

## 2. Repository and Environment State

### 2.1 Workspace Audit
- **Path:** `/Users/harimohan/Desktop/TrustCounsel AI`
- **Initial State:** Empty directory.
- **Git Status:** Initialized clean git repository on branch `main`.
- **Existing User Code:** None present. No legacy code or pre-existing technical debt to preserve.

### 2.2 System & Tooling Audit
| Component | Detected Version | Target Specification | Status |
|---|---|---|---|
| **Operating System** | macOS (Darwin ARM64/x86_64) | POSIX / Linux / macOS | Compatible |
| **Python** | 3.13.9 | Python 3.13+ | Match |
| **Node.js** | v25.9.0 | Node 20+ LTS / modern | Match |
| **Package Manager** | npm 11.12.1 | npm / pnpm | Match |
| **Docker Engine** | Docker 29.3.0 | Docker 24+ & Docker Compose v2 | Match |
| **Version Control** | Git 2.39+ | Git | Match |

---

## 3. Technology Stack Alignment

| Tier | Component | Technology Selected | Rationale & Trade-offs |
|---|---|---|---|
| **Frontend** | Framework & UI | React 19 + TypeScript + Vite + Tailwind CSS | Fast development cycles, static typing, low bundle overhead, accessible utility-first styling. |
| | State Management | TanStack Query v5 + React Router v7 | Server-cache invalidation, deterministic request lifecycle, declarative routing. |
| | Validation | Zod | Runtime schema validation matching backend Pydantic models. |
| | Testing | Vitest + React Testing Library + Playwright | Modern unit/component testing with browser-level E2E coverage. |
| **Backend** | API Engine | FastAPI (Python 3.13) | Asynchronous ASGI, native OpenAPI schema generation, high throughput, strong typing with Pydantic v2. |
| | ORM & DB | PostgreSQL 16 + pgvector + SQLAlchemy 2.0 + Alembic | Relational integrity for legal audits, ACID compliance, native vector similarity search + full-text search (FTS) hybrid retrieval. |
| | Caching & Tasks | Redis 7 + Background Worker Task Engine | Low-latency caching, session storage, and asynchronous document parsing/embedding pipelines. |
| | Orchestration | LangGraph | Stateful, cyclically-capable, typed multi-step agent workflow with checkpointing and human-in-the-loop pause/resume. |
| | Quality / Typing | Pytest + Ruff + mypy | Strict type-checking, sub-second linting, robust test suite. |
| **AI / Retrieval** | Model Providers | Pluggable Provider Interface (MockProvider + OpenAI/Anthropic/Ollama compatible) | Zero paid API dependencies for local development and CI; seamless switch to enterprise LLM endpoints in production. |
| | Verification | Hybrid Deterministic Verifier + Semantic Entailment Engine | Strict exact-match string/passage validation + NLI semantic verifier to detect hallucinations. |

---

## 4. Key Architectural Assumptions

1. **Self-Contained Local Execution:** Local development must function completely in mock mode without requiring live external cloud keys (e.g. OpenAI/Anthropic/AWS). A fully deterministic mock LLM & embedding provider is required.
2. **Multi-Tenancy & Workspace Isolation:** TrustCounsel AI is strictly multi-tenant by workspace. Document vectors, chunks, audit logs, evaluations, and conversation sessions must enforce tenant boundary checks at the database query layer (Row-Level Security or tenant-scoped filters on all queries).
3. **Evidence Precedence & Abstention:** LLMs cannot be trusted blindly. The system architecture will enforce an "abstain on low confidence / missing evidence" policy rather than allowing speculative or hallucinated legal analysis.
4. **Untrusted Input Protection:** Document text extracted from client-uploaded PDFs or TXTs is considered untrusted external data. Prompt injection countermeasures and strict tool permissions must isolate extracted text from system instructions.

---

## 5. Technical Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Hallucinated Citations** | Catastrophic for legal workflows; loss of user trust. | Multi-stage verification engine: strict chunk ID resolution, exact quotation matching, and claim-level evidence mapping before final response generation. |
| **Python 3.13 Library Compatibility** | High (some C-extensions or older AI libraries may lack pre-built wheels for 3.13). | Audit and pin modern versions of FastAPI, Pydantic v2, SQLAlchemy, psycopg3, and PyPDF/pdfplumber. Fallback pure-Python parsing where appropriate. |
| **Long Document Token Limits & Ingestion Latency** | High (500+ page contracts or discovery filings). | Chunking with hierarchical metadata (document, section, page, paragraph) and asynchronous background processing with status tracking (`UPLOADED -> PROCESSING -> INDEXED`). |
| **Tenant Data Leakage** | Critical (Confidential client legal documents). | Enforce workspace ID in every foreign key chain, session context middleware, and automated cross-tenant security test suites. |
| **Stale or Slow Verification Cycles** | Medium (Verification adds latency to research agent). | Two-tiered verifier: Fast deterministic checks (hash, substring match, exact citation) run synchronously; deep NLI checks run on flagged/controversial claims. |

---

## 6. Open Questions for Product Evolution

1. **Supported Formats in V1:** Scope PDF and TXT for Phase 1/MVP, deferring DOCX/DOC/OCR scanning pipelines to Phase 2.
2. **Human-in-the-Loop Threshold:** Should all low-confidence legal answers automatically enter the Review Queue, or can the user be shown the answer with an explicit "Unverified / High Risk" warning? *(Default assumption: Auto-route to Human Review queue when verification score < 0.85 or when contradictory evidence is identified).*
3. **Vector Dimension Default:** Default local mock embeddings to 384 dimensions (matching lightweight sentence-transformers) and allow configurable dimensions (1536 for OpenAI `text-embedding-3-small`, etc.) in pgvector table migrations.
