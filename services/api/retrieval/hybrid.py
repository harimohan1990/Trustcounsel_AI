import math

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.ai.providers import get_embedding_provider
from services.api.models.document import Document, DocumentChunk, DocumentStatus


class SearchCandidate:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        document_name: str,
        page_number: int,
        content: str,
        score: float,
        vector_rank: int | None = None,
        lexical_rank: int | None = None,
    ) -> None:
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_name = document_name
        self.page_number = page_number
        self.content = content
        self.score = score
        self.vector_rank = vector_rank
        self.lexical_rank = lexical_rank


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 < 1e-9 or norm2 < 1e-9:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


class HybridRetriever:
    @staticmethod
    async def retrieve(
        query: str,
        workspace_id: str,
        db: AsyncSession,
        top_k: int = 5,
        document_filter_ids: list[str] | None = None,
        min_similarity_threshold: float = 0.40,
    ) -> list[SearchCandidate]:
        """
        Executes hybrid search:
        1. Dense vector cosine similarity across authorized workspace chunks.
        2. Lexical keyword matching.
        3. Reciprocal Rank Fusion (RRF) combining the two ranking lists.
        """
        embedder = get_embedding_provider()
        query_vector = embedder.embed_query(query)
        keywords = [k.lower().strip() for k in query.split() if len(k) > 3]

        # 1. Fetch chunks belonging strictly to this workspace from INDEXED documents
        stmt = (
            select(DocumentChunk, Document.title, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                and_(
                    DocumentChunk.workspace_id == workspace_id,
                    Document.status == DocumentStatus.INDEXED,
                )
            )
        )
        if document_filter_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_filter_ids))

        result = await db.execute(stmt)
        rows = result.all()
        if not rows:
            return []

        # Vector scoring
        scored_by_vector = []
        for chunk, doc_title, doc_filename in rows:
            sim = cosine_similarity(query_vector, chunk.embedding)
            scored_by_vector.append((chunk, doc_title or doc_filename, sim))
        scored_by_vector.sort(key=lambda x: x[2], reverse=True)

        # Lexical scoring (keyword hit count & density)
        scored_by_lexical = []
        for chunk, doc_title, doc_filename in rows:
            content_lower = chunk.content.lower()
            hit_count = sum(content_lower.count(k) for k in keywords)
            scored_by_lexical.append((chunk, doc_title or doc_filename, hit_count))
        scored_by_lexical.sort(key=lambda x: x[2], reverse=True)

        # Build rank maps
        vector_ranks = {item[0].id: rank + 1 for rank, item in enumerate(scored_by_vector)}
        lexical_ranks = {item[0].id: rank + 1 for rank, item in enumerate(scored_by_lexical)}

        # Reciprocal Rank Fusion (RRF)
        # RRF_score = 1 / (60 + vector_rank) + 1 / (60 + lexical_rank)
        candidate_map: dict[str, SearchCandidate] = {}
        for chunk, doc_name, sim in scored_by_vector:
            vr = vector_ranks[chunk.id]
            lr = lexical_ranks[chunk.id]
            rrf_score = (1.0 / (60.0 + vr)) + (1.0 / (60.0 + lr))

            # Combine normalized score for threshold check
            normalized_score = max(sim, rrf_score * 30.0)

            candidate_map[chunk.id] = SearchCandidate(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=doc_name,
                page_number=chunk.page_number,
                content=chunk.content,
                score=round(normalized_score, 4),
                vector_rank=vr,
                lexical_rank=lr,
            )

        # Filter by threshold and sort by RRF score descending
        candidates = list(candidate_map.values())
        candidates.sort(key=lambda c: c.score, reverse=True)

        # Filter candidates meeting minimal threshold
        valid_candidates = [c for c in candidates if c.score >= min_similarity_threshold]
        return valid_candidates[:top_k]
