"""Broad, profile-aware and diversity-preserving retrieval for exploratory intent."""

from __future__ import annotations

from ..catalog import CatalogIndex, terms
from ..state import ProjectedState
from .exact import RetrievalResult


class BrowsingRetriever:
    def __init__(self, catalog: CatalogIndex) -> None:
        self.catalog = catalog

    def search(
        self,
        state: ProjectedState,
        profile: dict,
        limit: int = 10,
        question_pool_limit: int = 5000,
    ) -> RetrievalResult:
        pool = self.catalog.category_candidates(state.category or "")
        if not pool:
            pool = set(self.catalog.popular_ids[:question_pool_limit])
        category_terms = set(terms(state.category or ""))
        profile_terms = set(terms(" ".join(map(str, profile.get("preference_tags") or []))))
        scores: dict[int, float] = {}
        for product_id in pool:
            product = self.catalog.products[product_id]
            category_overlap = len(category_terms & (product.category_terms | product.title_terms))
            profile_overlap = len(profile_terms & product.content_terms)
            scores[product_id] = 3.0 * category_overlap + 0.35 * profile_overlap + 0.0001 * product.popularity
        ordered = sorted(
            pool,
            key=lambda product_id: (
                -scores[product_id],
                -self.catalog.products[product_id].popularity,
                self.catalog.products[product_id].parent_asin,
            ),
        )[:question_pool_limit]

        # Preserve the strongest six, then use category diversity for the tail.
        selected = list(ordered[: min(6, limit)])
        seen_categories = {self.catalog.products[item].category for item in selected}
        for product_id in ordered[len(selected):]:
            if len(selected) >= limit:
                break
            category = self.catalog.products[product_id].category
            if category not in seen_categories:
                selected.append(product_id)
                seen_categories.add(category)
        if len(selected) < limit:
            selected_set = set(selected)
            selected.extend(item for item in ordered if item not in selected_set and len(selected) < limit)
        return RetrievalResult(
            ranked_ids=tuple(selected),
            candidate_ids=tuple(ordered),
            scores=scores,
            matched_constraints=0,
        )

