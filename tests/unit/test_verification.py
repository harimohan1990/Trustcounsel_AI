from services.api.eval.metrics import (
    calculate_citation_precision,
    calculate_mrr,
    calculate_ndcg_at_k,
    calculate_precision_at_k,
    calculate_recall_at_k,
)
from services.api.trust.verifier import TrustEngine


def test_quote_fuzzy_match():
    source = "Section 14. Limitation of Liability. In no event shall either party's aggregate liability exceed $1,000,000."
    exact_quote = "either party's aggregate liability exceed $1,000,000"
    mismatch_quote = "unlimited punitive damages shall be awarded"

    assert TrustEngine.fuzzy_match_ratio(exact_quote, source) >= 0.95
    assert TrustEngine.fuzzy_match_ratio(mismatch_quote, source) < 0.50


def test_retrieval_and_eval_metrics():
    retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    relevant = {"doc2", "doc5"}

    recall = calculate_recall_at_k(retrieved, relevant, k=5)
    assert recall == 1.0

    precision = calculate_precision_at_k(retrieved, relevant, k=5)
    assert precision == 0.4  # 2 out of 5

    mrr = calculate_mrr(retrieved, relevant)
    assert mrr == 0.5  # first hit at rank 2 -> 1/2

    ndcg = calculate_ndcg_at_k(retrieved, relevant, k=5)
    assert ndcg > 0.6

    cit_prec = calculate_citation_precision(verified_count=10, total_count=10)
    assert cit_prec == 1.0
