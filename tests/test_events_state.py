from __future__ import annotations

from constraintgraph.events import EventKind, IntentEvent
from constraintgraph.state import SessionState, reduce_events


def event(kind: EventKind, attribute: str | None = None, value: str | None = None) -> IntentEvent:
    return IntentEvent(kind=kind, attribute=attribute, value=value, turn=1)


def test_event_replay_is_deterministic() -> None:
    events = [
        event(EventKind.ADD, "color", "black"),
        event(EventKind.REMOVE, "color", "black"),
        event(EventKind.ADD, "color", "navy"),
        event(EventKind.NO_PREFERENCE, "brand"),
    ]
    first = reduce_events(events)
    second = reduce_events(tuple(events))
    assert first.values("color") == second.values("color") == ["navy"]
    assert first.no_preferences == second.no_preferences == {"brand"}


def test_reset_increments_generation_and_clears_intent() -> None:
    session = SessionState("s", {})
    session.append([event(EventKind.SET_CATEGORY, value="shirts"), event(EventKind.ADD, "color", "black")])
    session.append([event(EventKind.RESET, value="intent"), event(EventKind.SET_CATEGORY, value="shoes")])
    state = session.current
    assert state.generation == 1
    assert state.category == "shoes"
    assert state.constraints == {}


def test_sessions_are_isolated() -> None:
    first = SessionState("first", {})
    second = SessionState("second", {})
    first.append([event(EventKind.ADD, "material", "leather")])
    assert first.current.values("material") == ["leather"]
    assert second.current.values("material") == []

