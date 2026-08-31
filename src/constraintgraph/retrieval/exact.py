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


class ExactRetriever:
    def __init__(self, catalog: CatalogIndex) -> None:
        self.catalog = catalog

    def search(self, state: ProjectedState, limit: int = 10, question_pool_limit: int = 5000) -> RetrievalResult:
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

        if matched_postings:
            strict = set.intersection(*matched_postings)
            pool = strict if strict else set.union(*matched_postings)
        else:
            pool = set()

        category_query_terms: tuple[str, ...] = ()
        if state.category:
            category_query_terms = terms(state.category)
            category_pool = self.catalog.category_candidates(state.category)
            if not pool:
                pool = category_pool
            elif category_pool:
                narrowed = pool & category_pool
                if narrowed:
                    pool = narrowed
        if not pool:
            pool = set(self.catalog.popular_ids[:question_pool_limit])

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
        return RetrievalResult(
            ranked_ids=tuple(ranked_all[:limit]),
            candidate_ids=tuple(ranked_all),
            scores=scored,
            matched_constraints=matched_constraints,
        )

