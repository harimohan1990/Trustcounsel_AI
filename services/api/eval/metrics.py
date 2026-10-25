import math


def calculate_recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if not relevant_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    hits = len(top_k.intersection(relevant_ids))
    return round(hits / len(relevant_ids), 4)


def calculate_precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if k <= 0:
        return 0.0
    top_k = set(retrieved_ids[:k])
    hits = len(top_k.intersection(relevant_ids))
    return round(hits / k, 4)


def calculate_mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    if not relevant_ids:
        return 1.0
    for idx, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return round(1.0 / (idx + 1), 4)
    return 0.0


def calculate_ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if not relevant_ids or k <= 0:
        return 1.0
    dcg = 0.0
    for idx, rid in enumerate(retrieved_ids[:k]):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(idx + 2)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant_ids), k)))
    if idcg < 1e-9:
        return 0.0
    return round(dcg / idcg, 4)


def calculate_citation_precision(verified_count: int, total_count: int) -> float:
    if total_count == 0:
        return 1.0
    return round(verified_count / total_count, 4)


def calculate_faithfulness(grounded_claims: int, total_claims: int) -> float:
    if total_claims == 0:
        return 1.0
    return round(grounded_claims / total_claims, 4)


def calculate_abstention_accuracy(correct_abstains: int, total_unanswerable: int) -> float:
    if total_unanswerable == 0:
        return 1.0
    return round(correct_abstains / total_unanswerable, 4)
