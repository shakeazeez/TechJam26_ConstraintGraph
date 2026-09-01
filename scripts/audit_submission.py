"""Fail fast on accidental secrets, private artifacts, or oversized tracked files."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANNED_TRACKED = {
    "PLAN.md",
    "data/catalog.jsonl",
    "data/catalog.jsonl.gz",
    "data/public_set.jsonl",
    "indexes/lexical.joblib",
    "results.json",
}
SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"(?:API_KEY|SECRET|TOKEN)\s*=\s*['\"]?[A-Za-z0-9_-]{16,}", re.I),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
MAX_TRACKED_BYTES = 5 * 1024 * 1024


def submission_files() -> list[Path]:
    """Return tracked and non-ignored untracked files that could enter the next commit."""

    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
    )
    return [ROOT / item.decode() for item in output.split(b"\0") if item]


def main() -> None:
    failures: list[str] = []
    files = submission_files()
    relative = {path.relative_to(ROOT).as_posix() for path in files}
    for banned in sorted(BANNED_TRACKED & relative):
        failures.append(f"banned tracked artifact: {banned}")
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        size = path.stat().st_size
        if size > MAX_TRACKED_BYTES:
            failures.append(f"oversized tracked file ({size} bytes): {rel}")
            continue
        payload = path.read_bytes()
        if any(pattern.search(payload) for pattern in SECRET_PATTERNS):
            failures.append(f"possible secret in: {rel}")
    if failures:
        raise SystemExit("submission audit failed:\n- " + "\n- ".join(failures))
    print(
        f"submission audit passed: {len(files)} tracked/non-ignored files, "
        "no banned artifacts or secret patterns"
    )


if __name__ == "__main__":
    main()
