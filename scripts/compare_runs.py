"""Compare aggregate metrics from official evaluator result files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FIELDS = ("sample_count", "hit_rate_at_10", "mrr", "mttc", "efficiency", "recommended_technical_score")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="+", type=Path)
    args = parser.parse_args()
    print("file\t" + "\t".join(FIELDS))
    for path in args.results:
        result = json.loads(path.read_text(encoding="utf-8"))
        print(path.name + "\t" + "\t".join(str(result.get(field, "")) for field in FIELDS))


if __name__ == "__main__":
    main()
