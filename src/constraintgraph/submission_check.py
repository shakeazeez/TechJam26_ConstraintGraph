"""Read-only submission contract and repository health checks."""

from __future__ import annotations

import argparse
import inspect
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

from .agent import Agent, QUESTION_TEXT


REQUIRED_DOCS = (
    "README.md",
    "requirements.txt",
    "reports/DEVPOST.md",
    "reports/AI_ASSISTED_DEVELOPMENT.md",
    "SUBMISSION_AUDIT.md",
)
SUSPICIOUS_NAMES = {".env", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}


@contextmanager
def _exact_mode() -> object:
    previous = os.environ.get("CONSTRAINTGRAPH_MODE")
    os.environ["CONSTRAINTGRAPH_MODE"] = "exact"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("CONSTRAINTGRAPH_MODE", None)
        else:
            os.environ["CONSTRAINTGRAPH_MODE"] = previous


def _validate_response(response: object, catalog_ids: set[str], top_k: int) -> list[str]:
    failures: list[str] = []
    if not isinstance(response, dict):
        return ["respond() did not return a dictionary"]
    if set(response) != {"message", "ask_attribute", "recommendations", "usage"}:
        failures.append("response keys differ from the submitted four-field schema")
    if not isinstance(response.get("message"), str):
        failures.append("message is not a string")
    if response.get("ask_attribute") not in {*QUESTION_TEXT, None}:
        failures.append("ask_attribute is not allowed")
    recommendations = response.get("recommendations")
    if not isinstance(recommendations, list):
        failures.append("recommendations is not a list")
        return failures
    asins = [item.get("parent_asin") for item in recommendations if isinstance(item, dict)]
    if len(asins) != len(recommendations):
        failures.append("a recommendation lacks an object parent_asin")
    if len(asins) > top_k:
        failures.append("more recommendations returned than top_k")
    if len(asins) != len(set(asins)):
        failures.append("duplicate recommendation ASINs returned")
    if any(asin not in catalog_ids for asin in asins):
        failures.append("recommendation outside the frozen catalog")
    usage = response.get("usage")
    if not isinstance(usage, dict) or any(
        not isinstance(usage.get(key), int) or usage[key] < 0
        for key in ("prompt_tokens", "completion_tokens")
    ):
        failures.append("usage is missing non-negative integer token counts")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only ConstraintGraph submission checks")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    args = parser.parse_args()
    root = Path.cwd()
    failures: list[str] = []
    passes: list[str] = []

    expected_reset = ["self", "session_id", "user_profile"]
    expected_respond = ["self", "session_id", "user_message", "turn", "top_k"]
    if list(inspect.signature(Agent.reset).parameters) == expected_reset:
        passes.append("Agent.reset signature")
    else:
        failures.append("Agent.reset signature")
    if list(inspect.signature(Agent.respond).parameters) == expected_respond:
        passes.append("Agent.respond signature")
    else:
        failures.append("Agent.respond signature")

    missing_docs = [name for name in REQUIRED_DOCS if not (root / name).is_file()]
    if missing_docs:
        failures.append("missing required docs: " + ", ".join(missing_docs))
    else:
        passes.append("required documentation files")

    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).split(b"\0")
    suspicious = [
        value.decode(errors="replace")
        for value in tracked
        if value and Path(value.decode(errors="replace")).name.casefold() in SUSPICIOUS_NAMES
    ]
    if suspicious:
        failures.append("suspicious tracked filenames: " + ", ".join(suspicious))
    else:
        passes.append("no obvious tracked secret filenames")

    if not args.catalog.is_file():
        failures.append(f"catalog is missing: {args.catalog}")
    else:
        with _exact_mode():
            agent = Agent(args.catalog)
        catalog_ids = set(agent.catalog.by_asin)
        catalog_snapshot = tuple(agent.catalog.by_asin)
        agent.reset("first", {})
        agent.reset("second", {})
        response = agent.respond(
            "first",
            "I'm looking for handbags. A key requirement is: leather.",
            1,
            10,
        )
        response_failures = _validate_response(response, catalog_ids, 10)
        failures.extend(response_failures)
        if not response_failures:
            passes.append("response contract and catalog-only unique ASINs")
        if agent.sessions["second"].current.values() or agent.sessions["second"].current.category:
            failures.append("session state leaked into a clean session")
        else:
            passes.append("session isolation smoke test")
        if tuple(agent.catalog.by_asin) != catalog_snapshot:
            failures.append("catalog identifiers changed during smoke test")
        else:
            passes.append("catalog remained unchanged")

    for item in passes:
        print(f"PASS  {item}")
    for item in failures:
        print(f"FAIL  {item}")
    print(f"\n{len(passes)} passed; {len(failures)} failed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
