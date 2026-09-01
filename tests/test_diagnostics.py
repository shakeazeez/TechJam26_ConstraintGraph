from __future__ import annotations

import json
from pathlib import Path

import pytest

from constraintgraph.agent import Agent
from constraintgraph.demo import SCENARIOS
from constraintgraph.parsing import parse_message
from constraintgraph.retrieval import BrowsingRetriever
from constraintgraph.state import ProjectedState


def _catalog(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.jsonl"
    rows = []
    colors = ("black", "blue", "red", "green")
    for index in range(24):
        color = colors[index % len(colors)]
        rows.append(
            {
                "parent_asin": f"ASIN{index:03d}",
                "title": f"{color.title()} leather boot {index}",
                "features": ["leather", f"color: {color}", f"feature {index % 6}"],
                "details": {"Department": "Adults"},
                "description": ["outdoor walking"],
                "categories": ["Clothing", "Shoes", "Boots"],
                "store": f"Brand {index % 3}",
                "average_rating": 4.0 + (index % 5) / 10,
                "rating_number": 10 + index,
                "price": 50 + index,
            }
        )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


@pytest.fixture()
def catalog_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("CONSTRAINTGRAPH_MODE", "exact")
    return _catalog(tmp_path)


def test_diagnostics_do_not_alter_response(catalog_path: Path) -> None:
    plain = Agent(catalog_path)
    traced = Agent(catalog_path, diagnostics=True)
    plain.reset("s", {})
    traced.reset("s", {})
    message = SCENARIOS["override"][0]
    assert plain.respond("s", message, 1, 10) == traced.respond("s", message, 1, 10)


def test_events_state_question_counts_and_recommendations_are_production_values(catalog_path: Path) -> None:
    agent = Agent(catalog_path, diagnostics=True)
    agent.reset("s", {})
    message = SCENARIOS["override"][0]
    expected_events = parse_message(message, 1, agent.sessions["s"].current)
    response = agent.respond("s", message, 1, 10)
    diagnostic = agent.last_diagnostics["s"]

    assert [item["kind"] for item in diagnostic["events"]] == [item.kind.value for item in expected_events]
    current = agent.sessions["s"].current
    assert diagnostic["projected_state"]["category"] == current.category
    assert diagnostic["projected_state"]["generation"] == current.generation
    assert diagnostic["projected_state"]["asked_attributes"] == current.asked_attributes

    retrieval = agent.retriever.search(current, limit=10)
    assert response["ask_attribute"] == diagnostic["selected_attribute"]
    assert diagnostic["retrieval"]["candidate_counts"]["question_pool"] == len(retrieval.candidate_ids)
    assert diagnostic["retrieval"]["candidate_counts"]["returned"] == len(response["recommendations"])
    assert [item["parent_asin"] for item in diagnostic["recommendations"]] == [
        item["parent_asin"] for item in response["recommendations"]
    ]


def test_no_preference_is_not_exposed_as_askable(catalog_path: Path) -> None:
    agent = Agent(catalog_path, diagnostics=True)
    agent.reset("s", {})
    agent.respond("s", SCENARIOS["override"][0], 1, 10)
    agent.respond("s", "I don't care about brand.", 2, 10)
    diagnostic = agent.last_diagnostics["s"]
    assert "brand" in diagnostic["projected_state"]["no_preferences"]
    assert "brand" not in {item["attribute"] for item in diagnostic["clarification_candidates"]}


def test_override_replaces_old_color_without_generation_change(catalog_path: Path) -> None:
    agent = Agent(catalog_path, diagnostics=True)
    agent.reset("s", {})
    for turn, message in enumerate(SCENARIOS["override"], start=1):
        agent.respond("s", message, turn, 10)
    diagnostic = agent.last_diagnostics["s"]
    assert [item["kind"] for item in diagnostic["events"]] == ["REMOVE", "ADD"]
    assert agent.sessions["s"].current.values("color") == ["blue"]
    assert diagnostic["projected_state"]["generation"] == 0


def test_evaluator_mode_is_silent_and_sessions_are_isolated(catalog_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    agent = Agent(catalog_path)
    capsys.readouterr()
    snapshot = tuple(agent.catalog.by_asin)
    agent.reset("first", {})
    agent.reset("second", {})
    agent.respond("first", SCENARIOS["override"][0], 1, 10)
    assert capsys.readouterr().out == ""
    assert agent.sessions["second"].current.values() == []
    assert agent.sessions["second"].current.category is None
    assert tuple(agent.catalog.by_asin) == snapshot


def test_demo_scenario_contains_messages_not_targets() -> None:
    source = Path("src/constraintgraph/demo.py").read_text(encoding="utf-8").casefold()
    assert "ground_truth" not in source
    assert "target_asin" not in source
    assert "public_set" not in source
    assert all(isinstance(message, str) for message in SCENARIOS["override"])


def test_browsing_trace_counts_real_collections(catalog_path: Path) -> None:
    agent = Agent(catalog_path)
    retriever = BrowsingRetriever(agent.catalog)
    state = ProjectedState(category="boots")
    plain = retriever.search(state, {}, limit=10)
    traced = retriever.search(state, {}, limit=10, diagnostics=True)
    assert traced.ranked_ids == plain.ranked_ids
    assert traced.candidate_ids == plain.candidate_ids
    assert traced.trace is not None
    assert traced.trace["route"] == "browsing"
    assert traced.trace["candidate_counts"]["question_pool"] == len(traced.candidate_ids)
    assert traced.trace["candidate_counts"]["returned"] == len(traced.ranked_ids)
