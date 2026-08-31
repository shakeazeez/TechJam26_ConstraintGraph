"""Run the unmodified official evaluator on named frozen public splits."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl, metric_summary
from starter.agent import Agent


def scored_summary(sessions: list[dict]) -> dict:
    summary = metric_summary(sessions)
    efficiency = max(0.0, min(1.0, (11.0 - float(summary["mttc"])) / 10.0))
    return {
        **summary,
        "efficiency": round(efficiency, 6),
        "recommended_technical_score": round(
            0.50 * summary["hit_rate_at_10"] + 0.30 * summary["mrr"] + 0.20 * efficiency,
            6,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--dataset", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("config/public_splits.json"))
    parser.add_argument("--splits", nargs="+", default=["development", "validation"])
    parser.add_argument("--output", type=Path, default=Path("artifacts/results_splits.json"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))["splits"]
    unknown = set(args.splits) - set(manifest)
    if unknown:
        raise SystemExit(f"unknown split names: {sorted(unknown)}")
    ids_by_split = {name: set(manifest[name]["sample_ids"]) for name in args.splits}
    selected_ids = set().union(*ids_by_split.values())
    samples = [sample for sample in load_jsonl(args.dataset) if str(sample["sample_id"]) in selected_ids]

    catalog_ids, categories, products = catalog_index(args.catalog)
    result = evaluate(Agent(args.catalog), samples, catalog_ids, categories, products)
    sessions_by_id = {str(session["sample_id"]): session for session in result["sessions"]}
    result["split_metrics"] = {
        name: scored_summary([sessions_by_id[sample_id] for sample_id in manifest[name]["sample_ids"]])
        for name in args.splits
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "sessions"}, indent=2))


if __name__ == "__main__":
    main()
