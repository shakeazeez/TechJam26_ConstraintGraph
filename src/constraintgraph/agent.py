"""Organizer-compatible zero-LLM ConstraintGraph agent."""

from __future__ import annotations

from pathlib import Path

from .catalog import CatalogIndex
from .clarification import choose_attribute
from .parsing import parse_message
from .retrieval import ExactRetriever
from .state import SessionState


QUESTION_TEXT = {
    "category": "Which product category should I focus on?",
    "material": "Do you have a material preference?",
    "color": "Do you have a preferred color?",
    "size": "Is there a size or fit requirement?",
    "style": "What style or fit do you prefer?",
    "brand": "Do you have a preferred brand?",
    "budget": "What budget should I stay within?",
    "feature": "Which product feature matters most?",
    "use_case": "What will you mainly use it for?",
    "other": "What other requirement matters most to you?",
}


class Agent:
    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog = CatalogIndex.from_jsonl(catalog_path)
        self.retriever = ExactRetriever(self.catalog)
        self.sessions: dict[str, SessionState] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self.sessions[session_id] = SessionState(session_id=session_id, profile=dict(user_profile or {}))

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        if session_id not in self.sessions:
            raise RuntimeError("reset must be called before respond")
        session = self.sessions[session_id]
        session.messages.append(user_message)
        session.append(parse_message(user_message, turn, session.current))
        result = self.retriever.search(session.current, limit=top_k)
        ask_attribute, _ = choose_attribute(self.catalog, result.candidate_ids, session.current)
        if ask_attribute:
            session.record_question(ask_attribute, turn, QUESTION_TEXT[ask_attribute])
            message = QUESTION_TEXT[ask_attribute]
        else:
            message = "These are the strongest matches for your current requirements."
        recommendations = [
            {"parent_asin": self.catalog.products[product_id].parent_asin}
            for product_id in result.ranked_ids
        ]
        return {
            "message": message,
            "ask_attribute": ask_attribute,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }

