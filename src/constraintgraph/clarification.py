"""Expected candidate-pool reduction and information-gain question policy."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .catalog import CatalogIndex, normalize_phrase
from .state import ProjectedState


ASKABLE_ATTRIBUTES = ("category", "material", "color", "size", "style", "brand", "budget", "feature", "use_case")


@dataclass(frozen=True, slots=True)
class AttributeUtility:
    attribute: str
    information_gain: float
    expected_remaining: float
    answer_rate: float
    adjusted_gain: float


def _partition_key(catalog: CatalogIndex, product_id: int, attribute: str, disclosed: set[str]) -> tuple[str, ...]:
    product = catalog.products[product_id]
    if attribute == "other":
        values = [value for value in product.signatures if normalize_phrase(value) not in disclosed]
        return tuple(normalize_phrase(value) for value in values[:2]) or ("<none>",)
    values = product.attributes.get(attribute, ())
    return tuple(sorted(normalize_phrase(value) for value in values)) or ("<none>",)


def attribute_utility(
    catalog: CatalogIndex,
    candidate_ids: Iterable[int],
    attribute: str,
    state: ProjectedState,
) -> AttributeUtility:
    ids = tuple(candidate_ids)
    if not ids:
        return AttributeUtility(attribute, 0.0, 0.0, 0.0, 0.0)
    disclosed = {normalize_phrase(value) for value in state.values()}
    counts = Counter(_partition_key(catalog, product_id, attribute, disclosed) for product_id in ids)
    total = len(ids)
    expected_remaining = sum(count * count for count in counts.values()) / total
    conditional_entropy = sum((count / total) * math.log2(max(1, count)) for count in counts.values())
    information_gain = math.log2(total) - conditional_entropy
    answer_rate = 1.0 - counts.get(("<none>",), 0) / total
    adjusted_gain = information_gain * (0.35 + 0.65 * answer_rate)
    if attribute == "other":
        adjusted_gain *= 0.95
    return AttributeUtility(attribute, information_gain, expected_remaining, answer_rate, adjusted_gain)


def choose_attribute(
    catalog: CatalogIndex,
    candidate_ids: Iterable[int],
    state: ProjectedState,
    include_other: bool = True,
) -> tuple[str | None, tuple[AttributeUtility, ...]]:
    ids = tuple(candidate_ids)
    if len(ids) <= 10:
        return None, ()
    excluded = set(state.asked_attributes) | state.no_preferences
    attributes = [attribute for attribute in ASKABLE_ATTRIBUTES if attribute not in excluded]
    if include_other and "other" not in excluded:
        attributes.append("other")
    utilities = tuple(attribute_utility(catalog, ids, attribute, state) for attribute in attributes)
    useful = [utility for utility in utilities if utility.answer_rate > 0.05 and utility.adjusted_gain > 0.02]
    if not useful:
        return None, utilities
    best = min(useful, key=lambda item: (-item.adjusted_gain, item.expected_remaining, item.attribute))
    return best.attribute, utilities

