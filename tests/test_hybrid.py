from __future__ import annotations

from constraintgraph.catalog import CatalogIndex
from constraintgraph.events import EventKind, IntentEvent
from constraintgraph.retrieval import ExactRetriever, HybridRetriever, LexicalIndex
from constraintgraph.state import reduce_events


def test_hybrid_prefers_title_and_constraint_alignment() -> None:
    products = [
        {"parent_asin": "A", "title": "Waterproof blue hiking boot", "features": ["leather", "color: blue"], "details": {}, "description": [], "categories": ["Shoes", "Hiking Boots"], "store": "A", "average_rating": 4.0, "rating_number": 1, "price": None},
        {"parent_asin": "B", "title": "Blue leather fashion boot", "features": ["leather", "color: blue"], "details": {}, "description": [], "categories": ["Shoes", "Fashion Boots"], "store": "B", "average_rating": 5.0, "rating_number": 100, "price": None},
    ]
    catalog = CatalogIndex.from_products(products)
    state = reduce_events([
        IntentEvent(EventKind.SET_CATEGORY, value="Hiking Boots"),
        IntentEvent(EventKind.ADD, "material", "leather"),
        IntentEvent(EventKind.ADD, "color", "color: blue"),
    ])
    exact = ExactRetriever(catalog)
    hybrid = HybridRetriever(catalog, exact, LexicalIndex(catalog))
    result = hybrid.search(state)
    assert catalog.products[result.ranked_ids[0]].parent_asin == "A"
