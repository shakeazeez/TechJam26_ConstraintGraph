from __future__ import annotations

from constraintgraph.events import EventKind, IntentEvent
from constraintgraph.routing import Route, choose_route
from constraintgraph.state import ProjectedState, reduce_events


def test_exploratory_message_uses_browsing_route() -> None:
    decision = choose_route("I'm looking for shoes, but I'm still exploring.", ProjectedState())
    assert decision.route is Route.BROWSING


def test_hard_constraint_uses_buying_route() -> None:
    state = reduce_events([IntentEvent(EventKind.ADD, "material", "leather", hardness="hard")])
    assert choose_route("Leather matters.", state).route is Route.BUYING


def test_soft_constraint_alone_remains_browsing() -> None:
    state = reduce_events([IntentEvent(EventKind.ADD, "style", "casual", hardness="soft")])
    assert choose_route("I'm considering something casual.", state).route is Route.BROWSING
