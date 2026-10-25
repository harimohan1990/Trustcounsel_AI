# Product Requirements Document (PRD): TrustCounsel AI
**Document ID:** SPEC-01-PRD  
**Version:** 1.0.0  
**Phase:** 1 — Product Requirements Specification  
**Status:** Baselined  
**Author:** Staff Software Engineer & Product Lead  

---

## 1. Problem Statement & Background

Legal professionals (attorneys, corporate counsel, paralegals, and compliance officers) handle large volumes of high-stakes documents, including contracts, regulatory filings, case law, and discovery disclosures. Existing generative AI tools suffer from critical shortcomings in legal settings:
1. **Hallucination & Fabrication:** Generating plausible-sounding citations, fabricated court decisions, or nonexistent contractual clauses.
2. **Lack of Verifiable Grounding:** Inability to pinpoint the exact clause, page, or paragraph justifying an assertion.
3. **Absence of Abstention:** Forcing an answer even when document evidence is absent, conflicting, or inconclusive.
4. **Weak Multi-Tenancy & Privacy:** Risk of leaking proprietary legal strategy or confidential counterparty documents across client matters or workspaces.
5. **No Auditable Traceability:** Inability for senior partners or compliance teams to verify how an answer was derived or require human sign-off before consequential legal actions.

**TrustCounsel AI** solves this by delivering an enterprise-grade, specification-driven legal intelligence platform featuring hybrid vector/keyword retrieval, claim-level truth verification, quote validation, contract comparison, stateful agentic workflows, human-in-the-loop review routing, and rigorous evaluation benchmarks.

---

## 2. Target Users & Personas

### Persona 1: Legal Researcher (Associate / Paralegal) — `USR-RES`
- **Role:** Researches legal queries against internal contract vaults and precedent libraries.
- **Goals:** Rapidly find relevant clauses, synthesize answers with clickable citations, and identify whether a point of law is directly supported or inferred.
- **Pain Points:** Spending hours manually cross-referencing citations; fear of hallucinated citations in client briefs.

### Persona 2: Corporate Legal Analyst (In-House Counsel) — `USR-ANA`
- **Role:** Reviews contracts, NDAs, Master Service Agreements (MSAs), and vendor agreements.
- **Goals:** Extract key clauses (governing law, indemnification, liability caps), compare modified drafts against standard templates, and detect non-standard risks.
- **Pain Points:** Redline comparison tools miss semantic shifts (e.g., subtle changes in termination conditions or uncapped indemnity).

### Persona 3: Legal Reviewer / Senior Partner — `USR-REV`
- **Role:** Gatekeeper responsible for sign-off on legal opinions, client deliverables, and high-risk analyses.
- **Goals:** Review flagged or low-confidence AI analyses, review cited evidence side-by-side, approve/reject/modify draft outputs, and attach binding audit notes.
- **Pain Points:** Distrust in black-box AI outputs; lack of time to inspect raw search outputs.

### Persona 4: Enterprise Administrator / Compliance Officer — `USR-ADM`
- **Role:** Manages team workspaces, user permissions, audit trails, evaluation runs, and model configurations.
- **Goals:** Ensure strict tenant isolation, review operational metrics (latency, token costs), run regression benchmarks, and monitor security events.
- **Pain Points:** Regulatory exposure, data leakage across client matters, uncontrollable LLM expenses.

---

## 3. Product Scope & MVP Definition

### 3.1 In-Scope (MVP Release)
1. **Workspace & Auth Management:** JWT-based authentication, RBAC (Administrator, Researcher, Reviewer), workspace-level data isolation.
2. **Document Ingestion Engine:** Asynchronous ingestion of PDF and TXT files, cryptographic content hashing, page-preserving text extraction, chunking with metadata, and hybrid indexing (pgvector + PostgreSQL full-text search).
3. **Legal Research Agent (LangGraph):** Multi-step research workflow with query validation, query expansion, hybrid retrieval, reranking, structured answer synthesis with explicit claim-citation mapping, and evidence inspection.
4. **Trust & Verification Engine:** Deterministic citation resolution (verifying chunk existence in authorized workspace), exact quote validation, claim-level evidence coverage assessment, conflict detection, and automated abstention on missing evidence.
5. **Document & Contract Intelligence:** Structured document summaries, automated extraction of 9 core clause categories, obligation extraction, side-by-side semantic contract comparison, and source-grounded risk indicators.
6. **Human Review Queue:** Workflow routing for low-confidence (<0.85), conflicting, or high-risk answers, enabling reviewer approve/reject/comment actions with immutable audit records.
7. **Evaluation & Observability Engine:** Standardized retrieval metrics (Recall@K, MRR, nDCG), answer quality metrics (citation precision, faithfulness, abstention correctness), operational metrics (latency, tokens, cost), and versioned evaluation dataset runner.
8. **Responsive Enterprise UI:** Modern React + Tailwind interface with three-panel research workspace, citation inspector, side-by-side diff view, review queue, and analytics dashboard.
9. **Deterministic Local Mock Mode:** Fully functional local development and testing environment without requiring live API keys or paid external services.

### 3.2 Explicitly Deferred Features (Post-MVP)
- Scanning OCR for image-only rasterized PDFs (Tesseract / AWS Textract integration).
- Native Microsoft Word (.docx) and Outlook (.msg/.eml) direct binary parsers.
- Multi-party live collaborative redlining (Google Docs style real-time CRDT).
- Direct external integration with third-party court docket APIs (PACER, LexisNexis, Westlaw).
- Multi-region active-active database replication.

---

## 4. Functional Requirements

### Module A: Authentication, Tenancy & Workspace Management
- **FR-001:** The system shall allow new users to register with an email, password, full name, and initial organization workspace.
- **FR-002:** The system shall authenticate users using secure passwords (argon2id or bcrypt) and issue signed, time-limited JWT tokens with refresh token rotation.
- **FR-003:** The system shall enforce workspace multi-tenancy. All database queries for documents, chunks, conversations, citations, reviews, and audit events MUST filter strictly by the authenticated user's active workspace ID.
- **FR-004:** The system shall support Role-Based Access Control (RBAC) with three standard roles: `ADMINISTRATOR`, `RESEARCHER`, and `REVIEWER`.
- **FR-005:** The system shall enforce document-level access permissions within a workspace (Confidential vs Public-to-Workspace).
- **FR-006:** The system shall log security audit events for registration, authentication failure, permission denial, document deletion, and review decisions.

### Module B: Document Ingestion Pipeline
- **FR-007:** The system shall accept PDF and TXT files up to 50MB per file with MIME-type and extension validation.
- **FR-008:** The system shall calculate an SHA-256 content hash upon upload to detect exact duplicates within the same workspace.
- **FR-009:** The system shall extract text while preserving explicit page boundaries, paragraph breaks, and document identity.
- **FR-010:** The system shall partition documents into overlapping text chunks (configurable: default 512 tokens with 64 token overlap) retaining metadata (`document_id`, `page_number`, `chunk_index`, `start_char`, `end_char`).
- **FR-011:** The system shall generate dense vector embeddings using the configured embedding provider (MockProvider or OpenAI/HuggingFace compatible).
- **FR-012:** The system shall maintain an explicit lifecycle state for each document: `UPLOADED -> PROCESSING -> INDEXED` or `FAILED`.
- **FR-013:** The system shall prevent search retrieval against documents in any state other than `INDEXED`.
- **FR-014:** The system shall provide an endpoint to delete a document and cascade-delete its chunks, embeddings, and cached search indexes.

### Module C: Legal Research Agent (LangGraph Orchestration)
- **FR-015:** The system shall accept natural-language legal research queries with optional filters for document collections or date ranges.
- **FR-016:** The system shall execute a stateful LangGraph workflow containing nodes: `validate_request` -> `plan_research` -> `retrieve_evidence` -> `rerank_evidence` -> `analyze_documents` -> `draft_response` -> `verify_claims` -> `assess_evidence` -> `human_review` (conditional) -> `finalize_response`.
- **FR-017:** The system shall perform hybrid search combining pgvector cosine similarity search and PostgreSQL `tsvector` full-text search with reciprocal rank fusion (RRF).
- **FR-018:** The system shall produce a structured response conforming to the `ResearchAnswerSchema`:
  - `answer` (markdown string)
  - `claims` (list of discrete factual statements)
  - `citations` (list of citations linking claims to `document_id`, `page_number`, `chunk_id`, and `quote_snippet`)
  - `limitations` (list of caveats and statutory constraints)
  - `confidence_assessment` (score from 0.00 to 1.00 with justification)
  - `requires_review` (boolean flag)
- **FR-019:** The system shall distinguish direct textual evidence from inferential reasoning in generated answers.
- **FR-020:** The system shall track and return stateful research conversation sessions with full message and run history.

### Module D: Document Intelligence & Contract Analysis
- **FR-021:** The system shall generate structured document summaries highlighting executive terms, parties, and limitations with source citations.
- **FR-022:** The system shall extract and classify clauses across 9 core categories:
  1. Parties
  2. Effective & Termination Dates
  3. Payment Terms
  4. Renewal Conditions
  5. Confidentiality Obligations
  6. Indemnification Provisions
  7. Liability Limitations
  8. Governing Law & Jurisdiction
  9. Termination Rights
- **FR-023:** The system shall extract contractual obligations as structured records containing: `responsible_party`, `action_required`, `trigger_or_deadline`, `source_citation`, and `status`.
- **FR-024:** The system shall compare two authorized contract documents (Version A vs Version B) and identify:
  - Added clauses
  - Removed clauses
  - Modified wording with diff snippets
  - Changed deadlines or financial obligations
  - Materiality classification (`LOW`, `MEDIUM`, `HIGH`)
- **FR-025:** The system shall generate explainable risk indicators linking specific problematic clauses to identifiable legal risks (e.g., uncapped indemnity, unilateral termination, missing breach cure period).
- **FR-041:** The system shall provide an automated Clause Risk Remediation & Negotiation Playbook engine that diagnoses clause-level liabilities and generates structured alternative language (Standard Preferred, Balanced Fallback, Aggressive Defense) with strategic negotiation rationale.

### Module E: Trust & Verification Engine
- **FR-026:** The system shall perform deterministic Citation Resolution, verifying that every cited `chunk_id` and `document_id` exists in the database and belongs to the user's workspace.
- **FR-027:** The system shall perform Quote Validation, verifying that quoted text snippets in citations appear verbatim or near-verbatim (Levenshtein similarity >= 0.95) within the source chunk.
- **FR-028:** The system shall perform Claim Verification, matching each discrete claim in the answer against supporting citations and scoring evidence coverage.
- **FR-029:** The system shall detect unsupported claims (claims with 0 verified supporting citations) and mark them as `UNSUPPORTED`.
- **FR-030:** The system shall detect contradictory evidence among retrieved passages and explicitly present conflicting viewpoints in the output.
- **FR-031:** The system shall enforce automated Abstention: If no relevant passages meet the minimum similarity threshold or if all candidate claims are unsupported, the agent shall return an explicit `INSUFFICIENT_EVIDENCE` result rather than hallucinating an answer.
- **FR-032:** The system shall automatically route responses to the Human Review Queue when:
  - Overall evidence confidence is < 0.85
  - Any material claim is flagged as unsupported or contradictory
  - A high-materiality risk is detected in contract analysis

### Module F: Human Review Workspace
- **FR-033:** The system shall maintain an active review queue of pending review tasks with priority scoring.
- **FR-034:** The system shall allow authorized Reviewers and Administrators to inspect the draft answer, claims, supporting citations, and side-by-side source text.
- **FR-035:** The system shall allow Reviewers to make an immutable review decision: `APPROVED`, `REJECTED`, or `REVISION_REQUESTED`, along with structured reviewer notes.
- **FR-036:** The system shall resume or close the paused LangGraph workflow run based on the human review decision.

### Module G: Evaluation & Observability
- **FR-037:** The system shall provide a versioned evaluation dataset management system storing gold-standard legal questions, reference answers, expected citations, and expected abstention cases.
- **FR-038:** The system shall execute automated evaluation runs calculating:
  - Retrieval: Recall@K, Precision@K, Mean Reciprocal Rank (MRR), nDCG@K
  - Answer Quality: Faithfulness score, Citation Precision, Citation Recall, Abstention Accuracy
  - Operational: P50/P95/P99 latency, Token usage (prompt + completion), Estimated financial cost
- **FR-039:** The system shall compare an evaluation run against a designated baseline run to report regression or improvement deltas.
- **FR-040:** The system shall log OpenTelemetry-compatible spans for every agent step (planning, retrieval, LLM call, verification).

---

## 5. Non-Functional Requirements (NFR)

### 5.1 Performance & Scalability
- **NFR-001 (API Latency):** Core CRUD endpoints (documents, sessions, reviews) shall respond in < 150ms at P95 under standard load.
- **NFR-002 (Hybrid Retrieval Latency):** pgvector + full-text search hybrid query over 50,000 chunks shall execute in < 250ms at P95.
- **NFR-003 (Document Ingestion Throughput):** Standard 20-page legal PDF shall be fully extracted, chunked, embedded, and indexed in < 5 seconds in local mock mode (< 15 seconds with external embedding API).
- **NFR-004 (Concurrency):** The API backend shall support a minimum of 50 concurrent active users on standard single-node development hardware.

### 5.2 Security, Privacy & Compliance
- **NFR-005 (Tenant Boundary Isolation):** Zero cross-tenant data leakage. Automated security test suite shall verify that User A in Workspace 1 receives HTTP 404/403 when requesting documents, chunks, runs, or citations of Workspace 2.
- **NFR-006 (Secret Hygiene):** No API keys, database passwords, or JWT secrets shall be hardcoded, logged in plain text, or exposed to the client.
- **NFR-007 (Prompt Injection Defense):** Document contents retrieved from RAG chunks shall be treated as untrusted data, enclosed in strict demarcation tags (`<untrusted_document_context>`), and barred from overriding system prompt directives.
- **NFR-008 (OWASP Top 10 Compliance):** Protection against SQL injection (enforced via SQLAlchemy parameterized queries), XSS (React sanitized rendering), CSRF, and broken object-level authorization (BOLA).

### 5.3 Reliability, Availability & Recovery
- **NFR-009 (Graceful Degradation):** If external model APIs experience rate limits (HTTP 429) or transient network timeouts (HTTP 5xx), the client shall execute exponential backoff with jitter (up to 3 retries).
- **NFR-010 (State Checkpointing):** LangGraph execution state shall be persisted to the database so interrupted runs can be inspected or resumed without restarting from scratch.
- **NFR-011 (Crash Isolation):** A failure in document extraction or embedding for one file shall not disrupt active search queries or background indexing of other documents.

### 5.4 Usability & Accessibility
- **NFR-012 (WCAG 2.1 AA Compliance):** UI components must maintain minimum contrast ratio (4.5:1 for normal text), full keyboard navigability (Tab, Enter, Escape for modals), and proper ARIA labels.
- **NFR-013 (Responsive Layout):** Responsive design supporting desktop monitors (1920x1080, 1440x900) and tablets (minimum 768px width).
- **NFR-014 (Citation Transparency):** Clicking any citation in an answer must highlight and scroll to the exact source quote snippet within the document viewer in < 100ms.

---

## 6. User Stories & Acceptance Criteria

### US-1: Verified Legal Research
**As a** Legal Researcher,  
**I want to** ask a research question over my workspace's uploaded agreements,  
**So that** I receive a coherent answer where every factual claim is linked to an exact source quote and page number.  
- **Acceptance Criteria:**
  1. GIVEN an indexed document containing indemnification limits, WHEN the user submits "What is the liability cap?", THEN the response cites the exact document ID, page, and paragraph.
  2. GIVEN a question on a topic not covered by any indexed document, WHEN the user submits the query, THEN the system returns an `INSUFFICIENT_EVIDENCE` result and does not fabricate citations.
  3. GIVEN the answer in the UI, WHEN the user clicks Citation [1], THEN the document viewer opens the cited page and highlights the exact matching snippet.

### US-2: Contract Version Redline & Risk Flagging
**As a** Legal Analyst,  
**I want to** compare Version 1 and Version 2 of an NDA,  
**So that** I can instantly see modified obligations, deleted liabilities, and high-risk clause changes.  
- **Acceptance Criteria:**
  1. GIVEN two authorized PDF/TXT contracts, WHEN the user initiates contract comparison, THEN the system produces a structured diff categorized into Added, Removed, and Modified clauses.
  2. GIVEN a modified clause where a mutual indemnity was changed to unilateral, THEN the system flags the clause with a `HIGH` risk indicator and an explanatory rationale.

### US-3: Human-in-the-Loop Sign-off
**As a** Senior Reviewer,  
**I want to** review AI research runs flagged with low confidence or conflicting evidence,  
**So that** unverified legal conclusions never reach the client without partner approval.  
- **Acceptance Criteria:**
  1. GIVEN an agent workflow where verification score is 0.72 (< 0.85), WHEN the workflow runs, THEN it transitions into `AWAITING_HUMAN_REVIEW` status and appears in the Review Queue.
  2. GIVEN a pending review task, WHEN the reviewer submits an `APPROVED` decision with notes, THEN the workflow transitions to `COMPLETED` and the decision is permanently recorded in the audit log.

---

## 7. Error Scenarios & Expected System Behaviors

| Scenario | Trigger / Cause | System Behavior | HTTP Code / UI Feedback |
|---|---|---|---|
| **Invalid File Type** | User uploads `.exe` or unsupported binary. | Reject immediately at upload gateway; do not save to disk or queue. | HTTP 400 with `INVALID_FILE_TYPE` and allowed extensions list. |
| **Corrupted PDF** | PDF has damaged header or EOF. | Worker catches parsing exception; marks document status as `FAILED` with detailed `error_message`. | HTTP 200 on status check; UI shows error badge with "File parsing failed". |
| **Cross-Tenant Access** | User in Workspace A requests Document ID from Workspace B. | Backend repository layer returns empty result / forbidden. | HTTP 404 (Not Found to avoid leaking entity existence) or HTTP 403. |
| **No Evidence Found** | Query matches 0 chunks above similarity threshold (0.60). | Research Agent enters Abstention branch in LangGraph; does not call generation LLM with zero context. | Returns structured `ResearchAnswer` with `confidence: 0.0`, `status: ABSTAINED`, and explanatory limitation note. |
| **Quote Mismatch** | LLM outputs a citation with a hallucinated quote snippet not in the chunk. | Trust Engine quote validator fails exact/fuzzy match check; marks citation as `UNVERIFIED_QUOTE` and lowers confidence. | Flags claim as unverified; routes run to Human Review Queue. |

---

## 8. Definition of Requirements Testability

Every requirement in this specification is mapped to an automated test category:
- `FR-001` through `FR-006`: Automated API integration tests (`tests/integration/test_auth.py`, `test_workspaces.py`).
- `FR-007` through `FR-014`: Unit and pipeline integration tests (`tests/unit/test_chunking.py`, `tests/integration/test_ingestion.py`).
- `FR-015` through `FR-020`: LangGraph workflow tests with mock LLM fixtures (`tests/integration/test_agent_workflow.py`).
- `FR-021` through `FR-025`: Document intelligence schema validation tests (`tests/unit/test_analysis.py`).
- `FR-026` through `FR-032`: Trust engine deterministic and fuzzy verifier tests (`tests/unit/test_verification.py`).
- `FR-033` through `FR-036`: Review queue transition tests (`tests/integration/test_review_queue.py`).
- `FR-037` through `FR-040`: Evaluation suite benchmarks (`tests/evaluation/test_eval_metrics.py`).
- `NFR-005` (Tenancy): Automated multi-tenant penetration test (`tests/security/test_tenant_isolation.py`).
