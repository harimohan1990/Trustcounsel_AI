# Requirements Traceability Matrix: TrustCounsel AI
**Document ID:** SPEC-TRACE  
**Version:** 1.0.0  
**Status:** Baselined  

---

## 1. Traceability Matrix

| Req ID | Description | Architecture Component | Data Model / Entities | API Endpoint | Test Target | Milestone |
|---|---|---|---|---|---|:---:|
| **FR-001** | User Registration & Workspace Creation | `AuthService` | `users`, `workspaces` | `POST /auth/register` | `test_auth.py` | M2 |
| **FR-002** | Secure JWT Authentication | `AuthService` | `users` | `POST /auth/login` | `test_auth.py` | M2 |
| **FR-003** | Strict Workspace Multi-Tenancy | `TenantContextMiddleware` | All Tables (`workspace_id`) | All Endpoints | `test_tenant_isolation.py` | M2 |
| **FR-004** | Role-Based Access Control (RBAC) | `AuthService` | `users.role` | All Endpoints | `test_rbac.py` | M2 |
| **FR-005** | Document Confidentiality Levels | `IngestionService` | `documents.classification` | `GET /documents` | `test_ingestion.py` | M3 |
| **FR-006** | Security Audit Logging | `AuditLogger` | `audit_events` | Internal Service | `test_audit_trail.py` | M2 |
| **FR-007** | PDF & TXT File Upload Validation | `IngestionService` | `documents` | `POST /documents` | `test_ingestion.py` | M3 |
| **FR-008** | SHA-256 Deduplication | `IngestionService` | `documents.content_hash` | `POST /documents` | `test_ingestion.py` | M3 |
| **FR-009** | Text & Page Boundary Extraction | `PDFExtractor` | `documents.page_count` | Ingestion Worker | `test_extraction.py` | M3 |
| **FR-010** | Overlapping Text Chunking | `TextChunker` | `document_chunks` | Ingestion Worker | `test_chunking.py` | M3 |
| **FR-011** | Dense Vector Embeddings | `EmbeddingProvider` | `document_chunks.embedding`| Ingestion Worker | `test_embeddings.py` | M3 |
| **FR-012** | Ingestion State Progression | `IngestionPipeline` | `documents.status` | `GET /documents/{id}/status`| `test_ingestion.py` | M3 |
| **FR-013** | Prevent Search on Unindexed Files | `RetrievalEngine` | `documents.status` | Hybrid Query | `test_retrieval.py` | M3 |
| **FR-014** | Cascade Document Deletion | `DocumentRepository` | Cascade FKs | `DELETE /documents/{id}` | `test_ingestion.py` | M3 |
| **FR-015** | Natural Language Query Input | `ResearchAgent` | `research_runs` | `POST /research` | `test_research_agent.py` | M4 |
| **FR-016** | LangGraph Stateful Workflow | `ResearchAgent (DAG)` | `research_runs` | `POST /research` | `test_agent_workflow.py`| M4 |
| **FR-017** | Hybrid Retrieval (pgvector + FTS) | `HybridRetriever` | `document_chunks` | Internal / Agent | `test_retrieval.py` | M3 |
| **FR-018** | Structured Research Response Schema | `ResponseSynthesizer` | `ResearchResponse` | `POST /research` | `test_research_agent.py` | M4 |
| **FR-019** | Evidence vs. Inference Distinction | `ResponseSynthesizer` | `ResearchResponse.limitations`| `POST /research` | `test_research_agent.py` | M4 |
| **FR-020** | Research Session History | `SessionService` | `research_sessions` | `GET /research/sessions` | `test_sessions.py` | M4 |
| **FR-021** | Document Executive Summary | `AnalysisService` | `document_analyses` | `POST /analysis/summarize`| `test_analysis.py` | M6 |
| **FR-022** | 9-Category Clause Extraction | `ClauseExtractor` | `extracted_clauses` | `POST /analysis/extract-clauses`| `test_analysis.py` | M6 |
| **FR-023** | Structured Obligation Extraction | `ObligationExtractor` | `obligations` | `POST /analysis/extract-obligations`| `test_analysis.py` | M6 |
| **FR-024** | Semantic Contract Comparison | `ContractDiffEngine` | In-memory Diff | `POST /analysis/compare` | `test_contract_diff.py`| M6 |
| **FR-025** | Explainable Risk Indicators | `RiskAnalyzer` | `RiskIndicators` | `POST /analysis/compare` | `test_contract_diff.py`| M6 |
| **FR-026** | Deterministic Citation Resolution | `TrustEngine` | `evidence_references` | `POST /verification/check`| `test_verification.py` | M5 |
| **FR-027** | Levenshtein Quote Validation | `TrustEngine` | `evidence_references` | `POST /verification/check`| `test_verification.py` | M5 |
| **FR-028** | Claim-Level Evidence Coverage | `TrustEngine` | `claims` | `POST /verification/check`| `test_verification.py` | M5 |
| **FR-029** | Unsupported Claim Flagging | `TrustEngine` | `claims.status` | `POST /verification/check`| `test_verification.py` | M5 |
| **FR-030** | Contradiction Detection | `TrustEngine` | `ResearchState.contradictions`| Agent Node | `test_verification.py` | M5 |
| **FR-031** | Automated Abstention Logic | `ResearchAgent` | `research_runs.status` | `POST /research` | `test_abstention.py` | M5 |
| **FR-032** | Automated Review Queue Routing | `ResearchAgent` | `review_tasks` | `POST /research` | `test_review_queue.py` | M5 |
| **FR-033** | Priority Review Queue | `ReviewService` | `review_tasks` | `GET /reviews` | `test_review_queue.py` | M7 |
| **FR-034** | Side-by-Side Review Evidence Inspection | Review Queue UI | `review_tasks`, chunks | `GET /reviews/{id}` | `test_review_queue.py` | M7 |
| **FR-035** | Reviewer Decision Audit Record | `ReviewService` | `review_decisions` | `POST /reviews/{id}/decision`| `test_review_queue.py` | M7 |
| **FR-036** | Checkpointed Workflow Resumption | `LangGraph Engine` | `research_runs` | Review Decision Action | `test_review_queue.py` | M7 |
| **FR-037** | Versioned Evaluation Datasets | `EvaluationEngine` | `evaluation_datasets` | `POST /evaluations/runs` | `test_eval_metrics.py` | M7 |
| **FR-038** | Automated Metric Calculation | `EvaluationEngine` | `evaluation_runs` | `GET /evaluations/runs/{id}`| `test_eval_metrics.py` | M7 |
| **FR-039** | Baseline Comparison & Deltas | `EvaluationEngine` | `evaluation_runs` | `GET /evaluations/compare`| `test_eval_metrics.py` | M7 |
| **FR-040** | OpenTelemetry Step Tracing | `TelemetryMiddleware` | `research_runs.traces` | `GET /research/{id}` | `test_telemetry.py` | M7 |
| **NFR-001** | Sub-150ms P95 API Latency | FastAPI Async Engine | DB Indexes | All Endpoints | `test_perf.py` | M8 |
| **NFR-002** | Sub-250ms Hybrid Search | pgvector + FTS | HNSW & GIN Indexes | Hybrid Search | `test_retrieval.py` | M3 |
| **NFR-003** | Ingestion Throughput (<5s) | Async Worker | Batched Embeddings | Ingestion Worker | `test_ingestion.py` | M3 |
| **NFR-005** | Strict Tenant Boundary Isolation | `TenantContextMiddleware` | Mandatory `workspace_id` | All Endpoints | `test_tenant_isolation.py` | M2, M8 |
| **NFR-007** | Prompt Injection Isolation | Agent Prompt Barrier | `<untrusted_document_context>`| Prompt Formatter | `test_prompt_injection.py`| M4, M8 |
| **NFR-010** | LangGraph State Checkpointing | LangGraph Checkpointer | DB State Store | Research Agent | `test_agent_workflow.py`| M4 |
| **NFR-012** | WCAG 2.1 AA UI Accessibility | React Design System | Tailwind CSS Tokens | UI Components | Component Tests | M2, M8 |
| **NFR-014** | Sub-100ms Citation Highlighting | React Document Viewer | Text Offset Indexing | Document Viewer | Frontend E2E | M5 |
