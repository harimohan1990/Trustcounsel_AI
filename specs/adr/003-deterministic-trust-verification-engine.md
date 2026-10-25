# ADR 003: Multi-Stage Deterministic and Semantic Trust & Verification Engine

## Status
Accepted

## Context
Commercial LLMs frequently generate fabricated citations, misattribute quotes, or make assertions that are not supported by the underlying source text. In legal applications, self-reported LLM confidence is meaningless and cannot be accepted as proof of correctness. We require a verifier that operates independently of the generation prompt.

## Decision
We implement a **multi-stage Trust & Verification Engine** combining deterministic checks and semantic validation:
1. **Stage 1 — Citation Entity Resolution (Deterministic):**
   - Verifies that every cited `chunk_id` and `document_id` exists in the database and belongs strictly to the authenticated user's workspace.
2. **Stage 2 — Quote Grounding Validation (Deterministic / Fuzzy Match):**
   - Validates that text presented in quotes matches the source chunk verbatim or within a tight Levenshtein distance ($\ge 0.95$ token similarity).
3. **Stage 3 — Claim-Level Evidence Coverage (Semantic / Rule-Based):**
   - Breaks generated answers into discrete atomic claims.
   - Maps each claim to its linked citations and verifies that at least one verified chunk supports the claim.
4. **Stage 4 — Conflict Detection & Automated Abstention:**
   - Detects contradictory statements across multiple retrieved sources.
   - If evidence coverage is 0 or average confidence $< 0.60$, the system automatically triggers an **Abstention** response (`INSUFFICIENT_EVIDENCE`).
   - If confidence is between $0.60$ and $0.85$, or if contradictions exist, the response is flagged for **Human Review**.

## Consequences
### Positive
- Prevents fabricated citations from ever reaching users unflagged.
- Deterministic checks run with sub-millisecond overhead.
- Provides actionable claim-by-claim verification badges in the frontend UI.

### Negative / Trade-offs
- Adds a discrete verification step to the request lifecycle, slightly increasing total round-trip time.
