"""Presentation CLI for inspecting real ConstraintGraph decisions."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agent import Agent


SCENARIOS = {
    "override": [
        "I'm looking for handbags. A key requirement is: leather.",
        "Black.",
        "Actually, make it blue.",
    ],
    "browsing": [
        "I'm looking for shoes, but I'm still exploring.",
    ],
    "adaptive-reset": [
        "I'm looking for handbags. A key requirement is: leather.",
        "Actually, ignore my earlier preference. What I need is: blue.",
    ],
}


class Palette:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def paint(self, code: str, value: object) -> str:
        text = str(value)
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def cyan(self, value: object) -> str:
        return self.paint("36", value)

    def green(self, value: object) -> str:
        return self.paint("32", value)

    def red(self, value: object) -> str:
        return self.paint("31", value)

    def yellow(self, value: object) -> str:
        return self.paint("33", value)

    def bold(self, value: object) -> str:
        return self.paint("1", value)


def _heading(palette: Palette, title: str) -> None:
    print(f"\n{palette.bold(title)}")


def _event_text(event: dict, palette: Palette) -> str:
    kind = event["kind"]
    marker = "+" if kind in {"ADD", "SET_CATEGORY"} else "-" if kind == "REMOVE" else "!"
    detail = ""
    if event.get("attribute"):
        detail += str(event["attribute"])
    if event.get("value"):
        detail += (" = " if detail else "") + str(event["value"])
    line = f"{marker} {kind:<13} {detail}".rstrip()
    if kind == "REMOVE":
        return palette.red(line)
    if kind in {"ADD", "SET_CATEGORY"}:
        return palette.green(line)
    if kind == "RESET":
        return palette.yellow(line)
    return palette.cyan(line)


def _render_state(state: dict) -> None:
    rows: list[tuple[str, str]] = []
    if state.get("category"):
        rows.append(("category", str(state["category"])))
    for attribute, constraints in state.get("constraints", {}).items():
        rows.append((attribute, ", ".join(str(item["value"]) for item in constraints)))
    for attribute in state.get("no_preferences", []):
        rows.append((attribute, "NO PREFERENCE"))
    if not rows:
        print("  (no active constraints)")
        return
    label_width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"  {label.title():<{label_width}}  {value}")


def _render_pipeline(retrieval: dict) -> None:
    counts = retrieval.get("candidate_counts", {})
    labels = {
        "catalog": "Catalog",
        "exact_intersection": "Exact intersection",
        "constraint_union": "Constraint union",
        "category_candidates": "Category candidates",
        "retrieval_pool": "Retrieval pool",
        "question_pool": "Question/rerank pool",
        "fused_ranking_pool": "Fused ranking pool",
        "returned": "Returned",
    }
    for key, label in labels.items():
        value = counts.get(key)
        if value is not None:
            print(f"  {label:<25} {int(value):>8,}")
    if counts.get("category_narrowed"):
        print("  Category intersection applied")


def _render_clarification(diagnostic: dict, palette: Palette) -> None:
    utilities = diagnostic.get("clarification_candidates", [])
    useful = [item for item in utilities if item["answer_rate"] > 0.05 and item["adjusted_gain"] > 0.02]
    ordered = sorted(
        useful,
        key=lambda item: (-item["adjusted_gain"], item["expected_remaining"], item["attribute"]),
    )[:5]
    if not ordered:
        print(f"  {diagnostic.get('no_question_reason') or 'No question selected.'}")
        return
    max_gain = max(float(item["information_gain"]) for item in ordered) or 1.0
    for item in ordered:
        bar_length = max(1, round(18 * float(item["information_gain"]) / max_gain))
        bar = "#" * bar_length
        print(
            f"  {item['attribute'].title():<12} {item['information_gain']:>6.3f} bits  "
            f"{palette.cyan(bar):<18}  expected {item['expected_remaining']:.1f}"
        )
    selected = diagnostic.get("selected_attribute")
    if selected:
        print(f"\n  {palette.green('SELECTED')} -> {str(selected).upper()}")
        print(f"  {diagnostic['selected_question']}")


def _render_results(diagnostic: dict, show_all: bool, debug_ranking: bool) -> None:
    recommendations = diagnostic.get("recommendations", [])
    visible = recommendations if show_all else recommendations[:3]
    for item in visible:
        print(f"  {item['rank']:>2}. {item['title'] or '(untitled product)'}")
        print(f"      {item['parent_asin']}  |  {item['category']}")
        if debug_ranking:
            components = item.get("score_components") or {"score": item.get("score")}
            values = ", ".join(
                f"{name}={float(value):.6g}" for name, value in components.items() if value is not None
            )
            print(f"      {values}")
    hidden = len(recommendations) - len(visible)
    if hidden:
        print(f"\n  + {hidden} more valid products")


def render_turn(diagnostic: dict, palette: Palette, show_all: bool, debug_ranking: bool) -> None:
    turn = diagnostic["turn"]
    print("\n" + "=" * 104)
    print(f" {palette.bold('ConstraintGraph'):<74} TURN {turn} / 10")
    print("=" * 104)
    _heading(palette, "YOU")
    print(diagnostic["message"])
    _heading(palette, "EVENTS THIS TURN")
    events = diagnostic.get("events", [])
    if events:
        for event in events:
            print(_event_text(event, palette))
    else:
        print("  (no intent event produced)")
    if any(event["kind"] in {"REMOVE", "RESET"} for event in events):
        print(f"\n{palette.yellow('INTENT CHANGE DETECTED')}")
    _heading(palette, "CURRENT INTENT")
    _render_state(diagnostic["projected_state"])
    print(f"  Generation: {diagnostic['projected_state']['generation']}")
    _heading(palette, "ROUTE")
    route = diagnostic["route"].upper()
    route_label = "precision-first" if route == "BUYING" else "explore-first"
    print(f"  {palette.cyan(route)} - {route_label}")
    print(f"  Reason: {diagnostic['route_reason']}")
    _heading(palette, "RETRIEVAL")
    retrieval = diagnostic.get("retrieval", {})
    for component in retrieval.get("components", []):
        mark = palette.green("[x]") if component["used"] else "[ ]"
        print(f"  {mark} {component['name']}")
    if retrieval.get("reason"):
        print(f"  {palette.yellow('Adaptive reason:')} {retrieval['reason']}")
    _heading(palette, "CANDIDATE PIPELINE")
    _render_pipeline(retrieval)
    _heading(palette, "NEXT-BEST QUESTION")
    _render_clarification(diagnostic, palette)
    _heading(palette, "TOP RESULTS")
    _render_results(diagnostic, show_all, debug_ranking)
    sys.stdout.flush()


def _run_message(
    agent: Agent,
    session_id: str,
    message: str,
    turn: int,
    palette: Palette,
    show_all: bool,
    debug_ranking: bool,
) -> dict:
    agent.respond(session_id, message, turn, 10)
    diagnostic = agent.last_diagnostics[session_id]
    render_turn(diagnostic, palette, show_all, debug_ranking)
    return diagnostic


def main() -> None:
    parser = argparse.ArgumentParser(description="Present real ConstraintGraph runtime diagnostics")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--interactive", action="store_true", help="type user messages interactively")
    mode.add_argument("--scenario", choices=sorted(SCENARIOS), default="override")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--show-all-results", action="store_true")
    parser.add_argument("--debug-ranking", action="store_true")
    parser.add_argument("--record-json", type=Path)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    palette = Palette(sys.stdout.isatty() and not args.no_color and "NO_COLOR" not in os.environ)
    print("Loading ConstraintGraph indexes...", flush=True)
    try:
        agent = Agent(args.catalog, diagnostics=True)
    except Exception as exc:
        raise SystemExit(f"Unable to load ConstraintGraph: {exc}") from None
    session_id = "demo"
    agent.reset(session_id, {})
    print("Ready.", flush=True)
    records: list[dict] = []

    try:
        if args.interactive:
            for turn in range(1, 11):
                message = input(f"\nYou [{turn}/10]> ").strip()
                if not message or message.casefold() in {"quit", "exit"}:
                    break
                records.append(
                    _run_message(
                        agent,
                        session_id,
                        message,
                        turn,
                        palette,
                        args.show_all_results,
                        args.debug_ranking,
                    )
                )
        else:
            for turn, message in enumerate(SCENARIOS[args.scenario], start=1):
                records.append(
                    _run_message(
                        agent,
                        session_id,
                        message,
                        turn,
                        palette,
                        args.show_all_results,
                        args.debug_ranking,
                    )
                )
    except (EOFError, KeyboardInterrupt):
        print("\nDemo ended.")
    except Exception as exc:
        raise SystemExit(f"Demo turn failed: {exc}") from None

    if args.record_json:
        args.record_json.parent.mkdir(parents=True, exist_ok=True)
        args.record_json.write_text(json.dumps({"turns": records}, indent=2) + "\n", encoding="utf-8")
        print(f"\nRecorded diagnostics: {args.record_json}")


if __name__ == "__main__":
    main()
