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

    def search(
        self,
        state: ProjectedState,
        limit: int = 10,
        question_pool_limit: int = 5000,
        diagnostics: bool = False,
    ) -> RetrievalResult:
        base = self.exact.search(
            state,
            limit=question_pool_limit,
            question_pool_limit=question_pool_limit,
            diagnostics=diagnostics,
        )
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
        ranked_ids = tuple(ranked[:limit])
        trace = None
        if diagnostics:
            base_counts = dict((base.trace or {}).get("candidate_counts", {}))
            base_counts["fused_ranking_pool"] = len(ranked)
            base_counts["returned"] = len(ranked_ids)
            trace = {
                "route": "buying",
                "strategy": "adaptive_lexical_fusion",
                "reason": "intent generation is greater than zero",
                "components": [
                    {"name": "exact constraint retrieval", "used": True},
                    {"name": "SQLite FTS5 BM25", "used": True},
                    {"name": "word TF-IDF", "used": True},
                    {"name": "character TF-IDF", "used": True},
                ],
                "candidate_counts": base_counts,
                "component_nonzero_candidates": {
                    "bm25": sum(1 for product_id in ids if lexical.bm25.get(product_id, 0.0) > 0.0),
                    "word_tfidf": sum(1 for product_id in ids if lexical.word_tfidf.get(product_id, 0.0) > 0.0),
                    "char_tfidf": sum(1 for product_id in ids if lexical.char_tfidf.get(product_id, 0.0) > 0.0),
                },
                "score_components": {
                    product_id: {
                        "exact_score": base.scores.get(product_id, 0.0),
                        "bm25": lexical.bm25.get(product_id, 0.0),
                        "word_tfidf": lexical.word_tfidf.get(product_id, 0.0),
                        "char_tfidf": lexical.char_tfidf.get(product_id, 0.0),
                        "fused_score": fused[product_id],
                    }
                    for product_id in ranked_ids
                },
            }
        return RetrievalResult(
            ranked_ids=ranked_ids,
            candidate_ids=tuple(ranked),
            scores=fused,
            matched_constraints=base.matched_constraints,
            trace=trace,
        )
