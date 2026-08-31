"""Print one complete public session while using the official evaluator unchanged."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl  # noqa: E402
from starter.agent import Agent  # noqa: E402


class TracingAgent:
    def __init__(self, catalog_path: Path) -> None:
        self.inner = Agent(catalog_path)

    def reset(self, session_id: str, user_profile: dict) -> None:
        self.inner.reset(session_id, user_profile)
        print("\nPROFILE")
        print(json.dumps(user_profile, indent=2))

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        print(f"\nTURN {turn} - CUSTOMER")
        print(user_message)
        response = self.inner.respond(session_id, user_message, turn, top_k)
        route = self.inner.sessions[session_id].current.route
        print(f"\nTURN {turn} - CONSTRAINTGRAPH [{route.upper()}]")
        print(response["message"])
        print(f"ask_attribute={response['ask_attribute']!r}")
        for rank, recommendation in enumerate(response["recommendations"], start=1):
            product_id = self.inner.catalog.by_asin[recommendation["parent_asin"]]
            product = self.inner.catalog.products[product_id]
            print(f"{rank:>2}. {product.parent_asin} - {product.title[:100]}")
        return response


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", default="public_0003")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--dataset", type=Path, default=Path("data/public_set.jsonl"))
    args = parser.parse_args()

    samples = [sample for sample in load_jsonl(args.dataset) if sample["sample_id"] == args.sample_id]
    if not samples:
        raise SystemExit(f"sample not found: {args.sample_id}")
    catalog_ids, categories, products = catalog_index(args.catalog)
    result = evaluate(TracingAgent(args.catalog), samples, catalog_ids, categories, products)
    session = result["sessions"][0]
    print("\nOFFICIAL EVALUATOR RESULT")
    print(json.dumps({key: value for key, value in session.items() if key != "sample_id"}, indent=2))
    print("\nThe Agent received messages and the safe profile only; the evaluator retained the target.")


if __name__ == "__main__":
    main()
