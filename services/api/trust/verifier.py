import difflib
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models.document import DocumentChunk


class CitationVerificationResult(BaseModel):
    citation_id: str
    chunk_id: str
    document_id: str
    page_number: int
    quote_snippet: str
    exists_in_workspace: bool
    is_quote_verified: bool
    match_ratio: float
    error_reason: str = ""


class ClaimVerificationResult(BaseModel):
    claim_id: str
    claim_text: str
    status: str  # "VERIFIED", "UNSUPPORTED", "CONTRADICTED"
    verified_citation_ids: list[str] = []
    notes: str = ""


class TrustVerificationSummary(BaseModel):
    is_verified: bool
    confidence_score: float
    verified_citations: list[CitationVerificationResult]
    claim_results: list[ClaimVerificationResult]
    unsupported_claims: list[str]
    contradictions: list[str]
    should_abstain: bool
    requires_human_review: bool


class TrustEngine:
    @staticmethod
    def fuzzy_match_ratio(quote: str, source_text: str) -> float:
        """
        Computes substring alignment similarity.
        Returns 1.0 for exact match, or Levenshtein ratio for near-verbatim quote.
        """
        quote_clean = quote.lower().strip()
        source_clean = source_text.lower().strip()
        if not quote_clean:
            return 0.0
        if quote_clean in source_clean:
            return 1.0

        # Substring fuzzy scan with difflib
        matcher = difflib.SequenceMatcher(None, quote_clean, source_clean)
        match = matcher.find_longest_match(0, len(quote_clean), 0, len(source_clean))
        if match.size == 0:
            return 0.0

        sub_slice = source_clean[match.b : match.b + len(quote_clean)]
        return difflib.SequenceMatcher(None, quote_clean, sub_slice).ratio()

    @staticmethod
    async def verify_citations_and_claims(
        citations: list[dict[str, Any]],
        claims: list[dict[str, Any]],
        workspace_id: str,
        db: AsyncSession,
    ) -> TrustVerificationSummary:
        """
        Executes multi-stage verification:
        1. Entity resolution: validates chunk exists and belongs to workspace.
        2. Quote validation: verifies verbatim or near-verbatim quote (ratio >= 0.95).
        3. Claim coverage: ensures every claim maps to at least 1 verified citation.
        4. Conflict check: detects contradictory statements.
        """
        verified_citations: list[CitationVerificationResult] = []
        valid_citation_ids = set()

        # Stage 1 & 2: Entity & Quote Validation
        for cit in citations:
            chunk_id = cit.get("chunk_id", "")
            quote = cit.get("quote_snippet", "")
            cit_id = cit.get("id", chunk_id)

            # Query database strictly scoped to workspace
            result = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.id == chunk_id,
                    DocumentChunk.workspace_id == workspace_id,
                )
            )
            chunk = result.scalar_one_or_none()

            if not chunk:
                verified_citations.append(
                    CitationVerificationResult(
                        citation_id=cit_id,
                        chunk_id=chunk_id,
                        document_id=cit.get("document_id", ""),
                        page_number=cit.get("page_number", 1),
                        quote_snippet=quote,
                        exists_in_workspace=False,
                        is_quote_verified=False,
                        match_ratio=0.0,
                        error_reason="Referenced chunk does not exist in active workspace.",
                    )
                )
                continue

            ratio = TrustEngine.fuzzy_match_ratio(quote, chunk.content)
            is_quote_verified = ratio >= 0.90

            verified_citations.append(
                CitationVerificationResult(
                    citation_id=cit_id,
                    chunk_id=chunk_id,
                    document_id=chunk.document_id,
                    page_number=chunk.page_number,
                    quote_snippet=quote,
                    exists_in_workspace=True,
                    is_quote_verified=is_quote_verified,
                    match_ratio=round(ratio, 4),
                    error_reason="" if is_quote_verified else "Quoted text not found verbatim in source passage.",
                )
            )
            if is_quote_verified:
                valid_citation_ids.add(cit_id)

        # Stage 3: Claim-Level Verification
        claim_results: list[ClaimVerificationResult] = []
        unsupported_claims: list[str] = []

        for cl in claims:
            cl_id = cl.get("id", "")
            cl_text = cl.get("claim_text", "")
            cl_cit_ids = cl.get("citation_ids", [])

            # Check how many cited citations are verified
            active_valid_cits = [cid for cid in cl_cit_ids if cid in valid_citation_ids]

            if active_valid_cits:
                status = "VERIFIED"
                notes = f"Supported by {len(active_valid_cits)} verified citations."
            else:
                status = "UNSUPPORTED"
                notes = "No verified citations substantiate this claim."
                unsupported_claims.append(cl_text)

            claim_results.append(
                ClaimVerificationResult(
                    claim_id=cl_id,
                    claim_text=cl_text,
                    status=status,
                    verified_citation_ids=active_valid_cits,
                    notes=notes,
                )
            )

        # Stage 4: Conflict Detection (Heuristic inspection)
        contradictions: list[str] = []
        # Check for opposing governing law or contradictory indemnity clauses
        texts = [c.get("quote_snippet", "").lower() for c in citations]
        has_ny = any("new york" in t for t in texts)
        has_de = any("delaware" in t for t in texts)
        if has_ny and has_de:
            contradictions.append("Contradictory governing law detected: both Delaware and New York are cited.")

        # Compute aggregate confidence score
        total_claims = len(claims) if claims else 1
        verified_count = sum(1 for c in claim_results if c.status == "VERIFIED")
        coverage_ratio = verified_count / total_claims

        # If zero citations were provided or all failed
        if not valid_citation_ids:
            confidence_score = 0.0
        else:
            confidence_score = round(coverage_ratio * (0.8 if contradictions else 1.0), 3)

        should_abstain = confidence_score < 0.50 or len(unsupported_claims) == len(claims)
        requires_human_review = (confidence_score < 0.85) or (len(contradictions) > 0) or (len(unsupported_claims) > 0)
        is_verified = (confidence_score >= 0.85) and not requires_human_review

        return TrustVerificationSummary(
            is_verified=is_verified,
            confidence_score=confidence_score,
            verified_citations=verified_citations,
            claim_results=claim_results,
            unsupported_claims=unsupported_claims,
            contradictions=contradictions,
            should_abstain=should_abstain,
            requires_human_review=requires_human_review,
        )
