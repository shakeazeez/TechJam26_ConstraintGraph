"""Deterministic parsing of customer messages into intent events."""

from __future__ import annotations

import re
import unicodedata

from .events import EventKind, IntentEvent
from .state import ProjectedState


MATERIALS = ("cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk", "rayon", "fabric")
COLORS = ("black", "white", "blue", "red", "pink", "green", "brown", "gray", "grey", "purple", "yellow", "orange", "navy")
SIZE_WORDS = ("size", "sizing", "width", "wide", "narrow", "small", "medium", "large", "xl", "xxl")
STYLE_WORDS = ("department", "style", "fit", "sleeve", "neck", "casual", "formal")
USE_CASE_WORDS = ("hiking", "running", "gym", "winter", "outdoor", "work", "walking", "wedding", "travel")


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value).strip(" \t\r\n.;,")


def infer_attribute(value: str) -> str:
    lowered = value.casefold()
    if "budget" in lowered or re.search(r"(?:\$|<=|under|below|less than|around)\s*\d", lowered):
        return "budget"
    if any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in MATERIALS):
        return "material"
    if "color" in lowered or "colour" in lowered or any(re.search(rf"\b{word}\b", lowered) for word in COLORS):
        return "color"
    if any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in SIZE_WORDS):
        return "size"
    if any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in STYLE_WORDS):
        return "style"
    if any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in USE_CASE_WORDS):
        return "use_case"
    return "feature"


def _event(
    kind: EventKind,
    *,
    turn: int,
    evidence: str,
    attribute: str | None = None,
    value: str | None = None,
    hardness: str = "hard",
    confidence: float = 1.0,
) -> IntentEvent:
    return IntentEvent(
        kind=kind,
        attribute=attribute,
        value=clean_text(value) if value else value,
        hardness=hardness,
        turn=turn,
        evidence=evidence,
        confidence=confidence,
    )


def _constraint_events(payload: str, *, turn: int, evidence: str, hardness: str = "hard") -> list[IntentEvent]:
    values = [clean_text(part) for part in payload.split(";") if clean_text(part)]
    return [
        _event(
            EventKind.ADD,
            attribute=infer_attribute(value),
            value=value,
            hardness=hardness,
            turn=turn,
            evidence=evidence,
        )
        for value in values
    ]


def parse_message(message: str, turn: int, current: ProjectedState | None = None) -> list[IntentEvent]:
    current = current or ProjectedState()
    text = clean_text(message)
    lowered = text.casefold()
    if not text:
        return []

    no_preference = re.search(
        r"(?:i\s+)?(?:do not|don't)\s+(?:have|care about|need)(?:\s+an?|\s+any)?(?:\s+additional)?\s+preference\s+(?:for|about)\s+([a-z_]+)|"
        r"(?:i\s+)?(?:do not|don't)\s+care\s+about\s+([a-z_]+)",
        lowered,
    )
    if no_preference:
        attribute = next(group for group in no_preference.groups() if group)
        return [_event(EventKind.NO_PREFERENCE, attribute=attribute, turn=turn, evidence=message)]

    forget = re.search(r"(?:forget|remove|drop)\s+(?:the\s+)?(.+?)(?:\s+requirement|\s+preference)?$", text, re.I)
    if forget:
        value = clean_text(forget.group(1))
        return [_event(EventKind.REMOVE, attribute=infer_attribute(value), value=value, turn=turn, evidence=message)]

    category_switch = re.search(r"(?:actually\s+)?(?:i(?:'m| am)\s+)?looking for\s+(.+?)\s+instead$", text, re.I)
    if category_switch:
        category = clean_text(category_switch.group(1))
        return [
            _event(EventKind.RESET, value="intent", turn=turn, evidence=message),
            _event(EventKind.SET_CATEGORY, value=category, turn=turn, evidence=message),
        ]

    replace_match = re.search(r"(?:actually[, ]+)?make it\s+(.+)$", text, re.I)
    if replace_match:
        value = clean_text(replace_match.group(1))
        attribute = infer_attribute(value)
        return [
            _event(EventKind.REMOVE, attribute=attribute, turn=turn, evidence=message),
            _event(EventKind.ADD, attribute=attribute, value=value, turn=turn, evidence=message),
        ]

    events: list[IntentEvent] = []
    full_override = bool(re.search(r"\b(?:ignore|forget)\s+my\s+earlier\s+(?:preference|requirements?|request|intent)\b", lowered))
    if full_override:
        events.append(_event(EventKind.RESET, value="intent", turn=turn, evidence=message))

    initial = re.search(r"(?:i(?:'m| am)\s+)?looking for\s+(.+?)(?:,\s+but|\.\s+|$)", text, re.I)
    if initial:
        category = clean_text(initial.group(1))
        if category and category.casefold() not in {"something", "a product", "an item"}:
            events.append(_event(EventKind.SET_CATEGORY, value=category, turn=turn, evidence=message, confidence=0.95))

    payload_match = re.search(r"(?:a key requirement is|what matters is|what i need is):\s*(.+)$", text, re.I)
    if payload_match:
        events.extend(_constraint_events(payload_match.group(1), turn=turn, evidence=message))
        return events

    if initial and ". " in text and "still exploring" not in lowered:
        remainder = clean_text(text.split(". ", 1)[1])
        if remainder and not remainder.casefold().startswith("a key requirement is"):
            events.extend(_constraint_events(remainder, turn=turn, evidence=message, hardness="soft"))
        return events

    if not events:
        direct_values: list[str] = []
        direct_values.extend(re.findall(rf"\b(?:{'|'.join(COLORS)})\b", lowered))
        direct_values.extend(re.findall(rf"\b(?:{'|'.join(MATERIALS)})\b", lowered))
        if len(direct_values) == 1:
            value = direct_values[0]
            events.extend(_constraint_events(value, turn=turn, evidence=message))
    return events

