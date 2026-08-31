"""Precision-preserving fusion of exact, BM25, and TF-IDF evidence."""

from __future__ import annotations

from ..catalog import CatalogIndex
from ..state import ProjectedState
from .exact import ExactRetriever, RetrievalResult
from .lexical import LexicalIndex, state_query


def _minmax(values: dict[int, float], ids: tuple[int, ...]) -> dict[int, float]:
    present = [values.get(product_id, 0.0) for product_id in ids]
    if not present:
        return {}
    low, high = min(present), max(present)
    if high <= low:
        return {product_id: 0.0 for product_id in ids}
    return {product_id: (values.get(product_id, 0.0) - low) / (high - low) for product_id in ids}


class HybridRetriever:
    def __init__(self, catalog: CatalogIndex, exact: ExactRetriever, lexical: LexicalIndex) -> None:
        self.catalog = catalog
        self.exact = exact
        self.lexical = lexical

    def search(self, state: ProjectedState, limit: int = 10, question_pool_limit: int = 5000) -> RetrievalResult:
        base = self.exact.search(state, limit=question_pool_limit, question_pool_limit=question_pool_limit)
        ids = base.candidate_ids
        lexical = self.lexical.score(state_query(state), ids)
        exact_norm = _minmax(base.scores, ids)
        bm25_norm = _minmax(lexical.bm25, ids)
        word_norm = _minmax(lexical.word_tfidf, ids)
        char_norm = _minmax(lexical.char_tfidf, ids)
        fused = {
            product_id: (
                8.0 * exact_norm.get(product_id, 0.0)
                + 1.20 * word_norm.get(product_id, 0.0)
                + 0.70 * char_norm.get(product_id, 0.0)
                + 0.35 * bm25_norm.get(product_id, 0.0)
                + 0.00001 * self.catalog.products[product_id].popularity
            )
            for product_id in ids
        }
        ranked = sorted(
            ids,
            key=lambda product_id: (
                -fused[product_id],
                -base.scores.get(product_id, 0.0),
                self.catalog.products[product_id].parent_asin,
            ),
        )
        return RetrievalResult(
            ranked_ids=tuple(ranked[:limit]),
            candidate_ids=tuple(ranked),
            scores=fused,
            matched_constraints=base.matched_constraints,
        )

