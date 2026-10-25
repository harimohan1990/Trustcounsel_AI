import hashlib
import os

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.ai.providers import get_embedding_provider
from services.api.ingestion.chunker import TextChunker
from services.api.ingestion.extractor import DocumentExtractor
from services.api.models.document import Document, DocumentChunk, DocumentStatus


class IngestionPipeline:
    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    async def process_document(document_id: str, db: AsyncSession) -> Document:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        try:
            # Transition to PROCESSING
            doc.status = DocumentStatus.PROCESSING
            await db.commit()
            await db.refresh(doc)

            if not os.path.exists(doc.storage_path):
                raise FileNotFoundError(f"Storage path {doc.storage_path} does not exist")

            with open(doc.storage_path, "rb") as f:
                file_bytes = f.read()

            # 1. Extract text and page numbers
            pages = DocumentExtractor.extract_from_bytes(file_bytes, doc.filename)
            doc.page_count = len(pages)

            # 2. Chunk text
            chunker = TextChunker(target_tokens=512, overlap_tokens=64)
            chunks_meta = chunker.chunk_pages(pages)

            if not chunks_meta:
                # If document is empty or unextractable
                doc.status = DocumentStatus.INDEXED
                await db.commit()
                return doc

            # 3. Generate embeddings
            embedder = get_embedding_provider()
            texts = [c.content for c in chunks_meta]
            embeddings = embedder.embed_documents(texts)

            # 4. Remove any prior chunks for this doc (idempotency)
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

            # 5. Insert new chunks
            for meta, emb in zip(chunks_meta, embeddings, strict=False):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    workspace_id=doc.workspace_id,
                    chunk_index=meta.chunk_index,
                    page_number=meta.page_number,
                    content=meta.content,
                    token_count=meta.token_count,
                    start_char=meta.start_char,
                    end_char=meta.end_char,
                    embedding=emb,
                )
                db.add(chunk)

            # Transition to INDEXED
            doc.status = DocumentStatus.INDEXED
            doc.error_message = None
            await db.commit()
            await db.refresh(doc)
            return doc

        except Exception as e:
            await db.rollback()
            # Update to FAILED with error message
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            await db.commit()
            raise e
