"""Intent routing with distinct Buying and Browsing behavior."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .state import ProjectedState


class Route(str, Enum):
    BUYING = "buying"
    BROWSING = "browsing"


@dataclass(frozen=True, slots=True)
class RouteDecision:
    route: Route
    reason: str


def choose_route(message: str, state: ProjectedState) -> RouteDecision:
    lowered = message.casefold()
    hard_constraints = [
        item
        for items in state.constraints.values()
        for item in items
        if item.hardness == "hard" and item.confidence >= 0.75
    ]
    if hard_constraints:
        return RouteDecision(Route.BUYING, "explicit hard constraint")
    if any(marker in lowered for marker in ("a key requirement is", "what matters is", "what i need is")):
        return RouteDecision(Route.BUYING, "high-intent requirement language")
    if "still exploring" in lowered:
        return RouteDecision(Route.BROWSING, "explicit exploratory language")
    return RouteDecision(Route.BROWSING, "no reliable hard constraint")

