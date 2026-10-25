# ADR 001: Hybrid Retrieval using PostgreSQL Full-Text Search and pgvector

## Status
Accepted

## Context
Legal research requires high semantic comprehension to understand legal concepts (e.g., "force majeure liabilities" matching "unforeseen commercial impracticability") while simultaneously demanding exact keyword and statutory reference precision (e.g., matching "Section 14.2(b)" or exact dollar thresholds like "$5,000,000").
Dedicated vector databases (such as Pinecone, Qdrant, or Milvus) add significant infrastructure complexity, dual-write synchronization risks, and tenant isolation overhead when combined with relational transactional legal data (e.g. users, workspaces, review decisions, audit logs).

## Decision
We choose **PostgreSQL 16 with the `pgvector` extension** combined with native PostgreSQL **Full-Text Search (`tsvector` + GIN indexing)**.
- Dense embeddings are stored in `document_chunks.embedding vector(384)` (or configurable dimensions) indexed via HNSW/IVFFlat.
- Full-text lexemes are stored in `document_chunks.tsv_content tsvector` indexed via GIN.
- A hybrid search query merges vector cosine distance and BM25/FTS ranking using **Reciprocal Rank Fusion (RRF)**:
  $$\text{RRF Score} = \frac{1}{60 + \text{rank}_{\text{vector}}} + \frac{1}{60 + \text{rank}_{\text{FTS}}}$$

## Consequences
### Positive
- Strict ACID transactional integrity: chunks and embeddings are inserted or deleted in the same database transaction as the document entity.
- Single database engine simplifies operations, local Docker Compose setup, and multi-tenant workspace filtering (`WHERE workspace_id = ...`).
- Eliminates dual-write desynchronization bugs between a relational DB and a separate vector DB.

### Negative / Trade-offs
- Very large-scale collections (> 50M chunks) may require dedicated index tuning or memory allocation for HNSW indexes compared to specialized distributed vector stores.
