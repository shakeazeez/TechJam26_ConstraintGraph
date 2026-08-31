from __future__ import annotations

import json
from pathlib import Path

from scripts.create_splits import create_manifest


def _samples() -> list[dict]:
    path = Path("data/public_set.jsonl")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_split_is_deterministic_disjoint_and_exhaustive() -> None:
    samples = _samples()
    first = create_manifest(samples)
    second = create_manifest(list(reversed(samples)))
    assert first == second

    ids_by_split = [set(value["sample_ids"]) for value in first["splits"].values()]
    assert sum(map(len, ids_by_split)) == 200
    assert not (ids_by_split[0] & ids_by_split[1])
    assert not (ids_by_split[0] & ids_by_split[2])
    assert not (ids_by_split[1] & ids_by_split[2])


def test_split_sizes_and_scenario_mix() -> None:
    manifest = create_manifest(_samples())
    assert manifest["splits"]["development"]["counts"]["total"] == 120
    assert manifest["splits"]["validation"]["counts"]["total"] == 40
    assert manifest["splits"]["pseudo_hidden"]["counts"]["total"] == 40
    assert manifest["splits"]["validation"]["counts"]["scenario"] == {
        "boundary": 2,
        "browsing": 16,
        "buying": 16,
        "intent_override": 6,
    }
