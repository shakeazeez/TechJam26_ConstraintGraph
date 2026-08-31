"""Thin organizer-compatible entry point for the packaged ConstraintGraph agent."""

from __future__ import annotations

import sys
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from constraintgraph.agent import Agent  # noqa: E402


__all__ = ["Agent"]
