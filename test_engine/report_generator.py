"""Generate a JSON summary from pytest-style test results."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class TestResult:
    name: str
    outcome: str
    duration_seconds: float
    message: str = ""


def write_report(results: Iterable[TestResult], destination: str | Path) -> Path:
    """Write test results and summary counts as a JSON report."""
    result_list = list(results)
    valid_outcomes = {"passed", "failed", "skipped"}
    invalid = [result.outcome for result in result_list if result.outcome not in valid_outcomes]
    if invalid:
        raise ValueError(f"unsupported test outcome: {invalid[0]}")
    if any(result.duration_seconds < 0 for result in result_list):
        raise ValueError("test durations cannot be negative")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            outcome: sum(result.outcome == outcome for result in result_list)
            for outcome in sorted(valid_outcomes)
        },
        "results": [asdict(result) for result in result_list],
    }
    path = Path(destination)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
