"""Create a deterministic, target-free 120/40/40 public-session split manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


SEED = "constraintgraph-public-split-v1"
SCENARIO_RATIOS = {"development": 0.60, "validation": 0.20, "pseudo_hidden": 0.20}


def _stable_key(sample_id: str) -> str:
    return hashlib.sha256(f"{SEED}\0{sample_id}".encode()).hexdigest()


def create_manifest(samples: list[dict]) -> dict:
    by_scenario: dict[str, list[dict]] = {}
    for sample in samples:
        by_scenario.setdefault(str(sample["scenario_type"]), []).append(sample)

    split_samples: dict[str, list[dict]] = {name: [] for name in SCENARIO_RATIOS}
    for scenario, rows in sorted(by_scenario.items()):
        ordered = sorted(rows, key=lambda row: _stable_key(str(row["sample_id"])))
        n = len(ordered)
        development_end = round(n * SCENARIO_RATIOS["development"])
        validation_end = development_end + round(n * SCENARIO_RATIOS["validation"])
        portions = {
            "development": ordered[:development_end],
            "validation": ordered[development_end:validation_end],
            "pseudo_hidden": ordered[validation_end:],
        }
        for split_name, portion in portions.items():
            split_samples[split_name].extend(portion)

    manifest: dict = {"seed": SEED, "splits": {}}
    for split_name, rows in split_samples.items():
        ordered = sorted(rows, key=lambda row: str(row["sample_id"]))
        manifest["splits"][split_name] = {
            "sample_ids": [str(row["sample_id"]) for row in ordered],
            "counts": {
                "total": len(ordered),
                "scenario": dict(sorted(Counter(str(row["scenario_type"]) for row in ordered).items())),
                "difficulty": dict(sorted(Counter(str(row.get("difficulty_bucket", "unknown")) for row in ordered).items())),
                "category": dict(sorted(Counter(str(row.get("category_bucket", "unknown")) for row in ordered).items())),
            },
        }

    all_ids = [sample_id for value in manifest["splits"].values() for sample_id in value["sample_ids"]]
    expected_ids = {str(sample["sample_id"]) for sample in samples}
    if len(all_ids) != len(set(all_ids)) or set(all_ids) != expected_ids:
        raise RuntimeError("split manifest is not disjoint and exhaustive")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("config/public_splits.json"))
    args = parser.parse_args()

    samples = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = create_manifest(samples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({name: value["counts"] for name, value in manifest["splits"].items()}, indent=2))


if __name__ == "__main__":
    main()

