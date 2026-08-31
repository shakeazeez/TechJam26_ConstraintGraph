"""Build and validate local derived indexes before evaluation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for path in (REPOSITORY_ROOT, SOURCE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from constraintgraph.catalog import CatalogIndex  # noqa: E402
from constraintgraph.retrieval import LexicalIndex  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("indexes/lexical.joblib"))
    args = parser.parse_args()
    catalog = CatalogIndex.from_jsonl(args.catalog)
    index = LexicalIndex.load_or_build(catalog, args.output)
    print(
        f"prepared {len(catalog.products):,} products; "
        f"word_shape={index.word_matrix.shape}; char_shape={index.char_matrix.shape}; "
        f"cache={args.output}"
    )


if __name__ == "__main__":
    main()
