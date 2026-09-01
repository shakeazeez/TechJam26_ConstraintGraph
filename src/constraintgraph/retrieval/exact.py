"""Exact signature retrieval with deterministic lexical/category fallback."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..catalog import CatalogIndex, normalize_phrase, terms
from ..state import ProjectedState


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    ranked_ids: tuple[int, ...]
    candidate_ids: tuple[int, ...]
    scores: dict[int, float]
    matched_constraints: int
    trace: dict[str, object] | None = None


class ExactRetriever:
    def __init__(self, catalog: CatalogIndex) -> None:
        self.catalog = catalog

    def search(
        self,
        state: ProjectedState,
        limit: int = 10,
        question_pool_limit: int = 5000,
        diagnostics: bool = False,
    ) -> RetrievalResult:
        scored: dict[int, float] = {}
        matched_postings: list[set[int]] = []
        matched_constraints = 0
        for constraints in state.constraints.values():
            for constraint in constraints:
                postings = self.catalog.phrase_postings.get(normalize_phrase(constraint.value))
                if not postings:
                    continue
                matched_constraints += 1
                posting_set = set(postings)
                matched_postings.append(posting_set)
                rarity = math.log1p(len(self.catalog.products) / max(1, len(posting_set)))
                hardness = 2.0 if constraint.hardness == "hard" else 1.0
                for product_id in posting_set:
                    scored[product_id] = scored.get(product_id, 0.0) + 20.0 * hardness * rarity

        strict_count: int | None = None
        union_count: int | None = None
        retrieval_strategy = "popularity_fallback"
        if matched_postings:
            strict = set.intersection(*matched_postings)
            strict_count = len(strict)
            if strict:
                pool = strict
                retrieval_strategy = "exact_intersection"
                if diagnostics:
                    union_count = len(set.union(*matched_postings))
            else:
                union = set.union(*matched_postings)
                union_count = len(union)
                pool = union
                retrieval_strategy = "constraint_overlap_fallback"
        else:
            pool = set()

        category_query_terms: tuple[str, ...] = ()
        category_pool_count: int | None = None
        category_narrowed = False
        if state.category:
            category_query_terms = terms(state.category)
            category_pool = self.catalog.category_candidates(state.category)
            category_pool_count = len(category_pool)
            if not pool:
                pool = category_pool
                if pool:
                    retrieval_strategy = "category_candidates"
            elif category_pool:
                narrowed = pool & category_pool
                if narrowed:
                    pool = narrowed
                    category_narrowed = True
        if not pool:
            pool = set(self.catalog.popular_ids[:question_pool_limit])
            retrieval_strategy = "popularity_fallback"

        retrieval_pool_count = len(pool)

        for product_id in pool:
            product = self.catalog.products[product_id]
            category_matches = len(set(category_query_terms) & (product.category_terms | product.title_terms))
            scored[product_id] = scored.get(product_id, 0.0) + 3.0 * category_matches + 0.0001 * product.popularity

        ranked_all = sorted(
            pool,
            key=lambda product_id: (
                -scored.get(product_id, 0.0),
                -self.catalog.products[product_id].popularity,
                self.catalog.products[product_id].parent_asin,
            ),
        )[:question_pool_limit]
        ranked_ids = tuple(ranked_all[:limit])
        trace = None
        if diagnostics:
            trace = {
                "route": "buying",
                "strategy": retrieval_strategy,
                "components": [
                    {"name": "exact constraint postings", "used": bool(matched_postings)},
                    {
                        "name": "constraint overlap fallback",
                        "used": retrieval_strategy == "constraint_overlap_fallback",
                    },
                    {"name": "category retrieval", "used": bool(state.category)},
                    {"name": "popularity fallback", "used": retrieval_strategy == "popularity_fallback"},
                ],
                "candidate_counts": {
                    "catalog": len(self.catalog.products),
                    "matched_posting_lists": len(matched_postings),
                    "exact_intersection": strict_count,
                    "constraint_union": union_count,
                    "category_candidates": category_pool_count,
                    "category_narrowed": category_narrowed,
                    "retrieval_pool": retrieval_pool_count,
                    "question_pool": len(ranked_all),
                    "returned": len(ranked_ids),
                },
                "score_components": {
                    product_id: {"exact_score": scored.get(product_id, 0.0)} for product_id in ranked_ids
                },
            }
        return RetrievalResult(
            ranked_ids=ranked_ids,
            candidate_ids=tuple(ranked_all),
            scores=scored,
            matched_constraints=matched_constraints,
            trace=trace,
        )
