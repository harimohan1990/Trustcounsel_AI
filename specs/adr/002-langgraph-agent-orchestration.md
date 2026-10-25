# ADR 002: Stateful Workflow Orchestration using LangGraph

## Status
Accepted

## Context
Legal research and contract analysis cannot be reliably executed as a single, opaque prompt or an uncontrolled autonomous agent loop (which tends to wander, hallucinate, or loop infinitely). The system requires:
1. Typed state passed immutably between processing nodes.
2. Explicit conditional routing (e.g. if evidence similarity is insufficient, branch directly to abstention).
3. Stateful human-in-the-loop pause and resume capabilities (review queue sign-off).
4. Full auditability of graph execution history for legal compliance.

## Decision
We adopt **LangGraph** (Python) as our primary workflow orchestration framework.
The workflow is defined as a typed state graph:
- **Graph State:** Contains user query, workspace context, extracted sub-queries, retrieved chunks, draft answer, verified citations, claim breakdown, verification scores, and human review signals.
- **Controlled Nodes:** Each node is a pure or deterministic function (`validate_request`, `plan_research`, `retrieve_evidence`, `rerank_evidence`, `analyze_documents`, `draft_response`, `verify_claims`, `assess_evidence`, `human_review`, `finalize_response`).
- **Checkpointing:** State checkpoints are persisted to allow pausing for human approval and resuming without re-running previous expensive LLM steps.

## Consequences
### Positive
- Predictable, deterministic execution paths with cycle bounds.
- Native human-in-the-loop interrupts and state resumption.
- Clear separation of concerns between planning, retrieval, generation, and verification.

### Negative / Trade-offs
- Slight dependency overhead compared to raw Python state machines, mitigated by strong typing and modular node structure.
