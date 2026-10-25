import io

from pypdf import PdfReader


class ExtractedPage:
    def __init__(self, page_number: int, text: str) -> None:
        self.page_number = page_number
        self.text = text


class DocumentExtractor:
    @staticmethod
    def extract_from_bytes(file_bytes: bytes, filename: str) -> list[ExtractedPage]:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return DocumentExtractor._extract_pdf(file_bytes)
        elif lower_name.endswith(".txt") or lower_name.endswith(".md"):
            return DocumentExtractor._extract_text(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {filename}. Only PDF and TXT are supported.")

    @staticmethod
    def _extract_pdf(file_bytes: bytes) -> list[ExtractedPage]:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages: list[ExtractedPage] = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append(ExtractedPage(page_number=idx + 1, text=text.strip()))
        return pages

    @staticmethod
    def _extract_text(file_bytes: bytes) -> list[ExtractedPage]:
        decoded = file_bytes.decode("utf-8", errors="replace")
        # Split into synthetic pages roughly every 3000 chars for TXT files
        PAGE_CHAR_SIZE = 3000
        pages: list[ExtractedPage] = []
        start = 0
        page_num = 1
        while start < len(decoded):
            end = min(start + PAGE_CHAR_SIZE, len(decoded))
            # Try to break at a newline
            if end < len(decoded):
                newline_idx = decoded.rfind("\n", start, end)
                if newline_idx != -1 and newline_idx > start:
                    end = newline_idx
            pages.append(ExtractedPage(page_number=page_num, text=decoded[start:end].strip()))
            start = end
            page_num += 1
        if not pages:
            pages.append(ExtractedPage(page_number=1, text=""))
        return pages
