from __future__ import annotations

import concurrent.futures
import os
import time
from pathlib import Path
from typing import Any

from .oracle import evaluate
from .paths import repo_root
from .results import merge_results, validate_results


def run_full_local_selftest(
    *,
    shard_count: int = 32,
    jobs: int | None = None,
    shard_timeout_seconds: float = 300,
    progress_every: int = 25,
    worker_max_cases: int = 1,
    output: Path | None = None,
    one_per_contract: bool = False,
    max_cases_per_shard: int | None = None,
) -> dict[str, Any]:
    del worker_max_cases  # Every evaluate call already isolates target lifecycle by shard.
    os.environ["OSBENCH_REFERENCE_MODE"] = "local"
    root = repo_root()
    jobs = jobs or min(shard_count, os.cpu_count() or 2)
    shard_dir = root / "artifacts/oracle/full-selftest-shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    def run(index: int) -> dict[str, Any]:
        return evaluate(
            target_spec="reference",
            reference_spec="reference",
            shard_count=shard_count,
            shard_index=index,
            one_per_contract=one_per_contract,
            max_cases=max_cases_per_shard,
            output=shard_dir / f"shard-{index:03d}.json",
            progress_every=progress_every,
        )

    paths: list[Path] = []
    errors: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {executor.submit(run, index): index for index in range(shard_count)}
        try:
            for future in concurrent.futures.as_completed(
                futures,
                timeout=max(shard_timeout_seconds, 1) * max(1, shard_count),
            ):
                index = futures[future]
                try:
                    result = future.result(timeout=shard_timeout_seconds)
                    paths.append(Path(result["output"]))
                except Exception as exc:
                    errors.append(f"shard {index}: {type(exc).__name__}: {exc}")
        except TimeoutError:
            pending = sorted(futures[future] for future in futures if not future.done())
            errors.append(f"timed out waiting for shards: {pending}")

    output = output or root / "results/full-local-selftest.json"
    if not paths:
        report = {
            "valid": False,
            "issues": errors or ["no shard completed"],
        }
        return {
            "output": str(output),
            "report": report,
            "scores": {},
            "selection": {},
            "elapsed_seconds": time.monotonic() - started,
            "passed": False,
        }
    merged = merge_results(sorted(paths), output)
    validation = validate_results(output)
    failed = sum(not case.get("passed", False) for case in merged.get("cases", []))
    return {
        "output": str(output),
        "report": {**validation, "shard_errors": errors},
        "scores": merged.get("scores", {}),
        "selection": merged.get("selection", {}),
        "elapsed_seconds": time.monotonic() - started,
        "passed": validation["valid"] and not errors and failed == 0,
    }
