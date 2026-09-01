"""Organizer-compatible zero-LLM ConstraintGraph agent."""

from __future__ import annotations

import os
from pathlib import Path

from .catalog import CatalogIndex
from .clarification import choose_attribute
from .events import EventKind, IntentEvent
from .parsing import parse_message
from .retrieval import BrowsingRetriever, ExactRetriever, HybridRetriever, LexicalIndex
from .routing import Route, choose_route
from .state import ProjectedState, SessionState


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
    def __init__(
        self,
        catalog_path: str | Path = "data/catalog.jsonl",
        *,
        diagnostics: bool = False,
    ) -> None:
        self.catalog = CatalogIndex.from_jsonl(catalog_path)
        self.retriever = ExactRetriever(self.catalog)
        self.browsing_retriever = BrowsingRetriever(self.catalog)
        self.mode = os.environ.get("CONSTRAINTGRAPH_MODE", "adaptive").casefold()
        if self.mode not in {"exact", "hybrid", "adaptive"}:
            raise ValueError("CONSTRAINTGRAPH_MODE must be exact, hybrid, or adaptive")
        cache_path = os.environ.get("CONSTRAINTGRAPH_INDEX_PATH", "indexes/lexical.joblib")
        self.lexical_index = (
            LexicalIndex.load_or_build(self.catalog, cache_path)
            if self.mode in {"hybrid", "adaptive"}
            else None
        )
        self.hybrid_retriever = (
            HybridRetriever(self.catalog, self.retriever, self.lexical_index)
            if self.lexical_index is not None
            else None
        )
        self.sessions: dict[str, SessionState] = {}
        self.diagnostics_enabled = diagnostics
        self.last_diagnostics: dict[str, dict] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self.sessions[session_id] = SessionState(session_id=session_id, profile=dict(user_profile or {}))
        self.last_diagnostics.pop(session_id, None)

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        if session_id not in self.sessions:
            raise RuntimeError("reset must be called before respond")
        session = self.sessions[session_id]
        session.messages.append(user_message)
        parsed_events = parse_message(user_message, turn, session.current)
        committed_events = session.append(parsed_events)
        decision = choose_route(user_message, session.current)
        route_events: list[IntentEvent] = []
        if session.current.route != decision.route.value:
            route_events = session.append([
                IntentEvent(
                    kind=EventKind.SET_ROUTE,
                    value=decision.route.value,
                    turn=turn,
                    evidence=decision.reason,
                )
            ])
        if decision.route is Route.BUYING:
            use_hybrid = self.mode == "hybrid" or (self.mode == "adaptive" and session.current.generation > 0)
            if use_hybrid and self.hybrid_retriever is not None:
                result = self.hybrid_retriever.search(
                    session.current,
                    limit=top_k,
                    diagnostics=self.diagnostics_enabled,
                )
            else:
                result = self.retriever.search(
                    session.current,
                    limit=top_k,
                    diagnostics=self.diagnostics_enabled,
                )
        else:
            result = self.browsing_retriever.search(
                session.current,
                session.profile,
                limit=top_k,
                diagnostics=self.diagnostics_enabled,
            )
        ask_attribute, utilities = choose_attribute(self.catalog, result.candidate_ids, session.current)
        question_event: IntentEvent | None = None
        if ask_attribute:
            question_event = session.record_question(ask_attribute, turn, QUESTION_TEXT[ask_attribute])
            message = QUESTION_TEXT[ask_attribute]
        else:
            message = "These are the strongest matches for your current requirements."
        recommendations = [
            {"parent_asin": self.catalog.products[product_id].parent_asin}
            for product_id in result.ranked_ids
        ]
        response = {
            "message": message,
            "ask_attribute": ask_attribute,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
        if self.diagnostics_enabled:
            current = session.current
            if len(result.candidate_ids) <= 10:
                no_question_reason = "question pool has 10 or fewer candidates"
            elif ask_attribute is None:
                no_question_reason = "no eligible attribute passed the production utility thresholds"
            else:
                no_question_reason = None
            self.last_diagnostics[session_id] = {
                "turn": turn,
                "message": user_message,
                "events": [_event_payload(event) for event in committed_events],
                "system_events": [
                    *[_event_payload(event) for event in route_events],
                    *([_event_payload(question_event)] if question_event else []),
                ],
                "projected_state": _state_payload(current),
                "route": decision.route.value,
                "route_reason": decision.reason,
                "retrieval": result.trace or {},
                "clarification_candidates": [
                    {
                        "attribute": utility.attribute,
                        "information_gain": utility.information_gain,
                        "expected_remaining": utility.expected_remaining,
                        "answer_rate": utility.answer_rate,
                        "adjusted_gain": utility.adjusted_gain,
                    }
                    for utility in utilities
                ],
                "selected_attribute": ask_attribute,
                "selected_question": message if ask_attribute else None,
                "no_question_reason": no_question_reason,
                "recommendations": [
                    {
                        "rank": rank,
                        "parent_asin": self.catalog.products[product_id].parent_asin,
                        "title": self.catalog.products[product_id].title,
                        "category": self.catalog.products[product_id].category,
                        "score": result.scores.get(product_id),
                        "score_components": (result.trace or {}).get("score_components", {}).get(product_id, {}),
                    }
                    for rank, product_id in enumerate(result.ranked_ids, start=1)
                ],
            }
        return response


def _event_payload(event: IntentEvent) -> dict:
    return {
        "kind": event.kind.value,
        "attribute": event.attribute,
        "value": event.value,
        "hardness": event.hardness,
        "turn": event.turn,
        "generation": event.generation,
        "evidence": event.evidence,
        "confidence": event.confidence,
    }


def _state_payload(state: ProjectedState) -> dict:
    return {
        "generation": state.generation,
        "route": state.route,
        "category": state.category,
        "constraints": {
            attribute: [
                {
                    "value": constraint.value,
                    "hardness": constraint.hardness,
                    "confidence": constraint.confidence,
                    "turn": constraint.turn,
                    "generation": constraint.generation,
                }
                for constraint in constraints
            ]
            for attribute, constraints in state.constraints.items()
        },
        "no_preferences": sorted(state.no_preferences),
        "asked_attributes": list(state.asked_attributes),
    }
