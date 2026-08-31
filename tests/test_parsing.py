from __future__ import annotations

from constraintgraph.events import EventKind, IntentEvent
from constraintgraph.parsing import parse_message
from constraintgraph.state import ProjectedState, reduce_events


def kinds(events: list[IntentEvent]) -> list[EventKind]:
    return [event.kind for event in events]


def test_make_it_blue_replaces_prior_color() -> None:
    current = reduce_events([IntentEvent(EventKind.ADD, "color", "black")])
    events = parse_message("Actually, make it blue.", 2, current)
    assert kinds(events) == [EventKind.REMOVE, EventKind.ADD]
    assert events[0].attribute == events[1].attribute == "color"
    assert events[1].value == "blue"


def test_forget_leather_removes_specific_constraint() -> None:
    events = parse_message("Forget the leather requirement.", 2)
    assert kinds(events) == [EventKind.REMOVE]
    assert events[0].attribute == "material"
    assert events[0].value == "leather"


def test_no_brand_preference() -> None:
    events = parse_message("I don't care about brand.", 2)
    assert kinds(events) == [EventKind.NO_PREFERENCE]
    assert events[0].attribute == "brand"


def test_category_switch_resets_incompatible_intent() -> None:
    events = parse_message("Actually I'm looking for shoes instead.", 3)
    assert kinds(events) == [EventKind.RESET, EventKind.SET_CATEGORY]
    assert events[1].value == "shoes"


def test_official_buying_message_extracts_category_and_requirement() -> None:
    events = parse_message(
        "I'm looking for Women Shoes. A key requirement is: waterproof construction.",
        1,
    )
    assert kinds(events) == [EventKind.SET_CATEGORY, EventKind.ADD]
    assert events[0].value == "Women Shoes"
    assert events[1].value == "waterproof construction"


def test_official_multi_constraint_reply() -> None:
    events = parse_message("For that, what matters is: leather; color: blue.", 2)
    assert [event.attribute for event in events] == ["material", "color"]


def test_official_full_override_resets_before_replacement() -> None:
    events = parse_message(
        "Actually, ignore my earlier preference. What I need is: polyester.",
        3,
    )
    assert kinds(events) == [EventKind.RESET, EventKind.ADD]
    assert events[1].attribute == "material"


def test_low_information_rejection_is_noop() -> None:
    assert parse_message("Those options are not quite right yet.", 2) == []

