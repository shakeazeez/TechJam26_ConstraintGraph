"""Append-only session event log and deterministic state projection."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from .events import EventKind, IntentEvent


@dataclass(frozen=True, slots=True)
class Constraint:
    attribute: str
    value: str
    hardness: str
    confidence: float
    turn: int
    generation: int
    evidence: str


@dataclass(slots=True)
class ProjectedState:
    generation: int = 0
    route: str = "browsing"
    category: str | None = None
    constraints: dict[str, list[Constraint]] = field(default_factory=dict)
    no_preferences: set[str] = field(default_factory=set)
    asked_attributes: list[str] = field(default_factory=list)

    def values(self, attribute: str | None = None) -> list[str]:
        if attribute is not None:
            return [item.value for item in self.constraints.get(attribute, [])]
        return [item.value for items in self.constraints.values() for item in items]


def reduce_events(events: Iterable[IntentEvent]) -> ProjectedState:
    state = ProjectedState()
    for event in events:
        state.generation = max(state.generation, event.generation)
        if event.kind is EventKind.RESET:
            if event.value in (None, "intent", "preferences"):
                state.constraints.clear()
                state.no_preferences.clear()
                state.asked_attributes.clear()
            if event.value in (None, "intent"):
                state.category = None
                state.route = "browsing"
            continue
        if event.kind is EventKind.SET_ROUTE:
            state.route = str(event.value)
            continue
        if event.kind is EventKind.SET_CATEGORY:
            state.category = event.value
            continue
        if event.kind is EventKind.ASK:
            if event.attribute and event.attribute not in state.asked_attributes:
                state.asked_attributes.append(event.attribute)
            continue
        if not event.attribute:
            continue
        if event.kind is EventKind.NO_PREFERENCE:
            state.constraints.pop(event.attribute, None)
            state.no_preferences.add(event.attribute)
            continue
        if event.kind is EventKind.REMOVE:
            existing = state.constraints.get(event.attribute, [])
            if event.value:
                target = event.value.casefold()
                existing = [item for item in existing if item.value.casefold() != target]
            else:
                existing = []
            if existing:
                state.constraints[event.attribute] = existing
            else:
                state.constraints.pop(event.attribute, None)
            continue
        if event.kind is EventKind.ADD and event.value:
            state.no_preferences.discard(event.attribute)
            item = Constraint(
                attribute=event.attribute,
                value=event.value,
                hardness=event.hardness,
                confidence=event.confidence,
                turn=event.turn,
                generation=event.generation,
                evidence=event.evidence,
            )
            existing = state.constraints.setdefault(event.attribute, [])
            if all(old.value.casefold() != item.value.casefold() for old in existing):
                existing.append(item)
    return state


@dataclass(slots=True)
class SessionState:
    session_id: str
    profile: dict
    events: list[IntentEvent] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    @property
    def current(self) -> ProjectedState:
        return reduce_events(self.events)

    @property
    def generation(self) -> int:
        return self.current.generation

    def append(self, events: Iterable[IntentEvent]) -> list[IntentEvent]:
        generation = self.generation
        committed: list[IntentEvent] = []
        for event in events:
            if event.kind is EventKind.RESET:
                generation += 1
            committed_event = replace(event, generation=generation)
            self.events.append(committed_event)
            committed.append(committed_event)
        return committed

    def record_question(self, attribute: str, turn: int, message: str = "") -> IntentEvent:
        event = IntentEvent(
            kind=EventKind.ASK,
            attribute=attribute,
            turn=turn,
            generation=self.generation,
            evidence=message,
        )
        self.events.append(event)
        return event
