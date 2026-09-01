"""Reproducible cold-start and isolated warm-turn latency benchmark."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import statistics
import sys
import time
from importlib import metadata
from pathlib import Path

from .agent import Agent


MESSAGES = (
    "I'm looking for handbags. A key requirement is: leather.",
    "I'm looking for shoes, but I'm still exploring.",
    "Blue.",
    "Actually, ignore my earlier preference. What I need is: waterproof construction.",
)


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _ram_bytes() -> int | None:
    if sys.platform != "win32":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return int(status.total_physical)
    return None


def _versions() -> dict[str, str]:
    result: dict[str, str] = {}
    for package in ("numpy", "scipy", "scikit-learn", "joblib"):
        try:
            result[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            result[package] = "not installed"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark ConstraintGraph without network work")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("benchmark_results.json"))
    parser.add_argument("--warmup", type=int, default=4)
    parser.add_argument("--n", type=int, default=40)
    args = parser.parse_args()
    if args.n < 2 or args.warmup < 0:
        raise SystemExit("--n must be at least 2 and --warmup must be non-negative")

    cache_path = Path(os.environ.get("CONSTRAINTGRAPH_INDEX_PATH", "indexes/lexical.joblib"))
    cache_prebuilt = cache_path.exists()
    started = time.perf_counter()
    agent = Agent(args.catalog)
    cold_start_seconds = time.perf_counter() - started

    for index in range(args.warmup):
        session_id = f"warmup_{index}"
        agent.reset(session_id, {})
        agent.respond(session_id, MESSAGES[index % len(MESSAGES)], 1, 10)

    latencies_ms: list[float] = []
    for index in range(args.n):
        session_id = f"measured_{index}"
        agent.reset(session_id, {})
        message = MESSAGES[index % len(MESSAGES)]
        started = time.perf_counter()
        agent.respond(session_id, message, 1, 10)
        latencies_ms.append((time.perf_counter() - started) * 1000.0)

    ram = _ram_bytes()
    payload = {
        "cold_start_seconds": cold_start_seconds,
        "warm_turn_latency_ms": {
            "median": statistics.median(latencies_ms),
            "p95": _percentile(latencies_ms, 0.95),
            "p99": _percentile(latencies_ms, 0.99),
            "minimum": min(latencies_ms),
            "maximum": max(latencies_ms),
        },
        "n": args.n,
        "warmup_turns": args.warmup,
        "platform": platform.platform(),
        "os": os.name,
        "cpu": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "ram_bytes": ram,
        "python": platform.python_version(),
        "dependencies": _versions(),
        "runtime_mode": agent.mode,
        "index_cache_path": str(cache_path),
        "index_cached_prebuilt": cache_prebuilt,
        "external_api_calls": 0,
        "methodology": (
            "Measured with time.perf_counter(). Cold start covers one Agent construction, including catalog parsing, "
            "cached TF-IDF loading when present, and in-memory SQLite FTS5 construction. Warm latency excludes "
            "startup and reset(), follows explicit warm-up turns, rotates four representative message types, and "
            "uses a freshly reset session for every timed respond() call. No network work occurs in timed regions."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
