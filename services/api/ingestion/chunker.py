from services.api.ingestion.extractor import ExtractedPage


class ChunkMetadata:
    def __init__(
        self,
        chunk_index: int,
        page_number: int,
        content: str,
        token_count: int,
        start_char: int,
        end_char: int,
    ) -> None:
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.content = content
        self.token_count = token_count
        self.start_char = start_char
        self.end_char = end_char


class TextChunker:
    """
    Overlapping chunker that preserves page boundaries and character positions.
    Configurable target tokens (default 512) and overlap (default 64).
    """
    def __init__(self, target_tokens: int = 512, overlap_tokens: int = 64) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_pages(self, pages: list[ExtractedPage]) -> list[ChunkMetadata]:
        chunks: list[ChunkMetadata] = []
        global_chunk_idx = 0

        for page in pages:
            text = page.text
            if not text:
                continue

            words = text.split()
            if not words:
                continue

            # Estimate ~1.3 tokens per word
            # Chunk by word count: target_words = int(target_tokens / 1.3)
            target_words = max(20, int(self.target_tokens / 1.3))
            overlap_words = max(5, int(self.overlap_tokens / 1.3))
            step = max(1, target_words - overlap_words)

            start_w = 0
            while start_w < len(words):
                end_w = min(start_w + target_words, len(words))
                chunk_text = " ".join(words[start_w:end_w])
                token_count = max(1, int(len(words[start_w:end_w]) * 1.3))

                # Find approximate char offsets in page text
                start_char = text.find(words[start_w]) if start_w < len(words) else 0
                end_char = start_char + len(chunk_text)

                chunks.append(
                    ChunkMetadata(
                        chunk_index=global_chunk_idx,
                        page_number=page.page_number,
                        content=chunk_text,
                        token_count=token_count,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )
                global_chunk_idx += 1

                if end_w >= len(words):
                    break
                start_w += step

        return chunks
