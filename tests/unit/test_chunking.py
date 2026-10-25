from services.api.ingestion.chunker import TextChunker
from services.api.ingestion.extractor import DocumentExtractor, ExtractedPage


def test_text_extractor():
    sample_text = "Section 1. Definitions.\n\nSection 2. Non-Disclosure Obligations.\nRecipient agrees to maintain confidentiality."
    pages = DocumentExtractor.extract_from_bytes(sample_text.encode("utf-8"), "test_contract.txt")
    assert len(pages) >= 1
    assert "Non-Disclosure" in pages[0].text
    assert pages[0].page_number == 1


def test_text_chunker_overlap():
    pages = [
        ExtractedPage(
            page_number=1,
            text="The liability cap shall not exceed the total fees paid by customer. The agreement survives termination for two years.",
        )
    ]
    chunker = TextChunker(target_tokens=10, overlap_tokens=4)
    chunks = chunker.chunk_pages(pages)

    assert len(chunks) >= 1
    for c in chunks:
        assert c.page_number == 1
        assert len(c.content) > 0
        assert c.token_count > 0
