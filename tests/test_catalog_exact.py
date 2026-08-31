from __future__ import annotations

from constraintgraph.catalog import CatalogIndex, derived_intent_values
from constraintgraph.events import EventKind, IntentEvent
from constraintgraph.retrieval import ExactRetriever
from constraintgraph.state import reduce_events


PRODUCTS = [
    {"parent_asin": "TARGET", "title": "Blue Trail Boot", "features": ["leather", "Waterproof construction", "Non-slip sole"], "details": {"Department": "Womens"}, "description": ["For hiking"], "categories": ["Clothing, Shoes & Jewelry", "Women", "Shoes", "Hiking Boots"], "store": "Trail Co", "average_rating": 4.5, "rating_number": 100, "price": 80.0},
    {"parent_asin": "OTHER", "title": "Black Fashion Boot", "features": ["leather", "Decorative buckle"], "details": {"Department": "Womens"}, "description": ["For parties"], "categories": ["Clothing, Shoes & Jewelry", "Women", "Shoes", "Fashion Boots"], "store": "Style Co", "average_rating": 4.8, "rating_number": 500, "price": 90.0},
]


def test_derived_signatures_prioritize_visible_material_and_color() -> None:
    values = derived_intent_values(PRODUCTS[0])
    assert values[0] == "leather"
    assert values[1] == "color: blue"


def test_multiple_constraints_retrieve_target_over_popular_collision() -> None:
    catalog = CatalogIndex.from_products(PRODUCTS)
    state = reduce_events([
        IntentEvent(EventKind.SET_CATEGORY, value="Shoes Hiking Boots"),
        IntentEvent(EventKind.ADD, "material", "leather"),
        IntentEvent(EventKind.ADD, "color", "color: blue"),
    ])
    result = ExactRetriever(catalog).search(state)
    assert catalog.products[result.ranked_ids[0]].parent_asin == "TARGET"

