"""
Thread-safe helper for logging quick metrics.
"""

from pathlib import Path
from time import time
import json, threading, os

_METRICS = {
    "total_wall_seconds": 0.0,
    "clarification_prompts": 0,
    "openai_tokens_in": 0,
    "openai_tokens_out": 0,
}
_LOCK = threading.Lock()
_LOG_FILE = Path(os.getenv("BAE_METRICS_LOG", "logs/metrics.jsonl"))
_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def add_time(delta: float):             # ⏱
    with _LOCK:
        _METRICS["total_wall_seconds"] += delta


def add_tokens(inp: int, out: int):     # 💰
    with _LOCK:
        _METRICS["openai_tokens_in"]  += inp
        _METRICS["openai_tokens_out"] += out


def inc_clarification():                # ❔
    with _LOCK:
        _METRICS["clarification_prompts"] += 1


def flush_snapshot():
    """Write one JSON line with cumulative metrics."""
    with _LOCK:
        with _LOG_FILE.open("a") as f:
            f.write(json.dumps(_METRICS, indent=2) + "\n")