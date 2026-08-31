from __future__ import annotations

from constraintgraph.catalog import CatalogIndex
from constraintgraph.clarification import attribute_utility, choose_attribute
from constraintgraph.state import ProjectedState


def product(asin: str, material: str, color: str) -> dict:
    return {"parent_asin": asin, "title": f"{color} sample", "features": [material], "details": {}, "description": [], "categories": ["Clothing", "Samples"], "store": "Same Brand", "average_rating": 4.0, "rating_number": 1, "price": None}


def test_material_has_more_information_than_constant_color() -> None:
    catalog = CatalogIndex.from_products([
        product("A", "cotton", "black"), product("B", "cotton", "black"),
        product("C", "leather", "black"), product("D", "leather", "black"),
    ])
    state = ProjectedState()
    assert attribute_utility(catalog, range(4), "material", state).information_gain > attribute_utility(catalog, range(4), "color", state).information_gain


def test_question_policy_skips_already_asked_and_no_preference() -> None:
    catalog = CatalogIndex.from_products([product(str(i), "cotton" if i % 2 else "leather", "black") for i in range(12)])
    state = ProjectedState(asked_attributes=["material"], no_preferences={"brand"})
    selected, utilities = choose_attribute(catalog, range(12), state, include_other=False)
    assert selected not in {"material", "brand"}
    assert all(item.attribute not in {"material", "brand"} for item in utilities)

