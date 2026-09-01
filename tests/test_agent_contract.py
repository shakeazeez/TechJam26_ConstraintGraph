from __future__ import annotations

import inspect

from constraintgraph.agent import Agent, QUESTION_TEXT


def test_official_method_signatures_are_preserved() -> None:
    assert list(inspect.signature(Agent.reset).parameters) == ["self", "session_id", "user_profile"]
    assert list(inspect.signature(Agent.respond).parameters) == [
        "self",
        "session_id",
        "user_message",
        "turn",
        "top_k",
    ]


def test_allowed_question_attributes_match_contract() -> None:
    assert set(QUESTION_TEXT) == {
        "category",
        "material",
        "color",
        "size",
        "style",
        "brand",
        "budget",
        "feature",
        "use_case",
        "other",
    }
