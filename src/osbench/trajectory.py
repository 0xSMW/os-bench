from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from .paths import repo_root
from .util import read_json, write_json


class TrajectoryRecorder:
    def __init__(self, path: Path, run_id: str, data: dict[str, Any]) -> None:
        self.path = Path(path)
        self.run_id = run_id
        self.data = data

    @classmethod
    def create(
        cls,
        path: Path | None = None,
        *,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "TrajectoryRecorder":
        run_id = run_id or f"trajectory-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        path = path or repo_root() / "artifacts" / "trajectories" / f"{run_id}.json"
        if path.exists():
            value = read_json(path)
            existing_run_id = str(value.get("run_id") or run_id)
            return cls(path, existing_run_id, value)
        data = {
            "schema_version": "osbench.trajectory.v1",
            "run_id": run_id,
            "created_at_unix": int(time.time()),
            "metadata": metadata or {},
            "events": [],
        }
        write_json(path, data)
        return cls(path, run_id, data)

    def append(self, event: str, **fields: Any) -> dict[str, Any]:
        record = {
            "sequence": len(self.data["events"]),
            "event": event,
            "timestamp_unix_ns": time.time_ns(),
            **fields,
        }
        self.data["events"].append(record)
        write_json(self.path, self.data)
        return record

    record = append


def summarize_trajectory(path: Path) -> dict[str, Any]:
    data = read_json(path)
    events = data.get("events", [])
    first_timestamp = events[0].get("timestamp_unix_ns") if events else None
    last_timestamp = events[-1].get("timestamp_unix_ns") if events else None
    elapsed = (
        (last_timestamp - first_timestamp) / 1_000_000_000
        if isinstance(first_timestamp, int) and isinstance(last_timestamp, int)
        else 0.0
    )
    return {
        "run_id": data.get("run_id"),
        "events": len(events),
        "event_types": sorted({event.get("event") for event in events}),
        "first": events[0] if events else None,
        "last": events[-1] if events else None,
        "elapsed_seconds": elapsed,
    }


def result_metrics(
    *,
    started_ns: int,
    contract_results: dict[str, Any],
    evaluated_cases: int,
    oracle_queries: int,
    target_spec: str,
) -> dict[str, Any]:
    passed = [identifier for identifier, value in contract_results.items() if value.get("passed")]
    return {
        "wall_clock_seconds": (time.monotonic_ns() - started_ns) / 1_000_000_000,
        "evaluated_cases": evaluated_cases,
        "oracle_queries": oracle_queries,
        "passed_contracts": len(passed),
        "target": target_spec,
        "time_to_first_boot": None,
        "time_to_first_userspace": None,
        "build_attempts": None,
        "test_attempts": 1,
        "regressions_introduced": None,
        "regressions_repaired": None,
        "tokens": None,
        "source_code_growth": None,
        "disk_image_growth": None,
    }
