# Performance & Reliability Specification: TrustCounsel AI
**Document ID:** SPEC-09-PERF  
**Version:** 1.0.0  
**Phase:** 4 — Test Specifications  
**Status:** Approved & Baselined  

---

## 1. Performance Targets & Budgets

| Metric | Target (P50) | Target (P95) | Hard SLA (P99) |
|---|:---:|:---:|:---:|
| **Authentication / Me / Session List** | 25ms | 80ms | 150ms |
| **Document Ingestion (20 Pages)** | 2.5s | 4.5s | 8.0s |
| **Hybrid Search (50k Chunks)** | 45ms | 120ms | 250ms |
| **Trust Verification Check** | 10ms | 30ms | 60ms |
| **End-to-End Research Run (Mock Mode)** | 400ms | 850ms | 1,500ms |
| **Contract Redline Diffing** | 150ms | 350ms | 600ms |

---

## 2. Scalability & Resource Allocation

### 2.1 Concurrency Capacity
- The FastAPI application running with 4 Uvicorn workers shall handle a minimum of **100 concurrent requests/second** on standard 4-vCPU hardware.
- Database connection pool configured with SQLAlchemy:
  - `pool_size = 20`
  - `max_overflow = 30`
  - `pool_timeout = 30s`
  - `pool_recycle = 1800s`

### 2.2 Redis Cache Policies
- **User Sessions:** TTL 15 minutes, refreshed on activity.
- **RRF Search Results Cache:** TTL 5 minutes keyed by `hash(workspace_id, query_terms)`. Invalidation triggered upon any new document indexing in the workspace.
- **Rate Limiter:** Token bucket with 1-second replenishment rate.

---

## 3. Reliability, Resilience & Failure Recovery

### 3.1 Model Provider Resilience
1. **Exponential Backoff with Full Jitter:**
   - Retries on HTTP 429 (Rate Limit) and HTTP 503 (Provider Unavailable).
   - Base interval: 500ms; Max interval: 8000ms; Max retries: 3.
   - Formula: $t = \text{random}(0, \min(M, B \times 2^{\text{attempt}}))$.
2. **Circuit Breaker:**
   - If 5 consecutive model requests fail or timeout within 60 seconds, the circuit breaker opens for 30 seconds, returning an informative HTTP 503 to prevent cascading queue exhaustion.

### 3.2 Ingestion Failure Isolation
- Document parsing occurs in isolated worker execution frames.
- If a corrupt PDF triggers a segmentation fault or memory leak, the worker supervisor isolates the failure, records the exact error in `documents.error_message`, and updates `documents.status = 'FAILED'`.
- Unprocessed documents remain in queue for retry without affecting ongoing queries.

---

## 4. Load & Stress Testing Methodology

A reproducible benchmark script (`scripts/run_load_test.py`) simulates concurrent legal researcher traffic:
1. **Step 1:** Pre-seeds database with 20 sample contracts (1,000 total chunks).
2. **Step 2:** Spawns 25 concurrent simulated clients executing search, research queries, and clause extraction loops.
3. **Step 3:** Measures throughput (RPS), error rate (must be 0.0%), and latency percentiles over a 2-minute sustained load window.
