"""Capture non-secret reproducibility metadata for a final evaluator run."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from importlib import metadata
from pathlib import Path


def _command(*args: str) -> str | None:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture non-secret final-run environment metadata")
    parser.add_argument("--output", type=Path, default=Path("environment_capture.json"))
    parser.add_argument(
        "--execution-command",
        default="python -m evaluator.local_evaluator --output artifacts/results.json",
    )
    args = parser.parse_args()
    dependencies: dict[str, str] = {}
    for package in ("constraintgraph", "numpy", "scipy", "scikit-learn", "joblib", "pytest"):
        try:
            dependencies[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            dependencies[package] = "not installed"
    payload = {
        "git_commit": _command("git", "rev-parse", "HEAD"),
        "git_status_short": _command("git", "status", "--short"),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cpu": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "dependencies": dependencies,
        "execution_command": args.execution_command,
        "notes": "No environment-variable values or secrets are captured.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
