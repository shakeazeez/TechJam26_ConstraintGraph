"""Typed immutable events used as the source of truth for conversational state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EventKind(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    NO_PREFERENCE = "NO_PREFERENCE"
    RESET = "RESET"
    SET_CATEGORY = "SET_CATEGORY"
    SET_ROUTE = "SET_ROUTE"
    ASK = "ASK"


@dataclass(frozen=True, slots=True)
class IntentEvent:
    kind: EventKind
    attribute: str | None = None
    value: str | None = None
    hardness: str = "hard"
    turn: int = 0
    generation: int = 0
    evidence: str = ""
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between zero and one")
        if self.kind in {EventKind.ADD, EventKind.REMOVE} and not self.attribute:
            raise ValueError(f"{self.kind.value} requires an attribute")
        if self.kind is EventKind.ADD and not self.value:
            raise ValueError("ADD requires a value")
        if self.kind in {EventKind.NO_PREFERENCE, EventKind.ASK} and not self.attribute:
            raise ValueError(f"{self.kind.value} requires an attribute")
        if self.kind is EventKind.SET_CATEGORY and not self.value:
            raise ValueError("SET_CATEGORY requires a value")
        if self.kind is EventKind.SET_ROUTE and self.value not in {"buying", "browsing"}:
            raise ValueError("SET_ROUTE requires buying or browsing")
