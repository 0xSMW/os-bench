from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .paths import repo_root
from .util import read_json, write_json


def summarize(path: Path) -> dict[str, Any]:
    result = read_json(path)
    scores = result.get("scores", {})
    cases = result.get("cases", [])
    unsupported = result.get("unsupported", [])
    return {
        "run_id": result.get("run_id"),
        "reference": result.get("reference_target"),
        "candidate": result.get("candidate_target"),
        "requested": result.get("selection", {}).get("requested_cases"),
        "evaluated": len(cases),
        "unsupported": len(unsupported),
        "failed": sum(not case.get("passed", False) for case in cases),
        "OSCorrect": scores.get("OSCorrect"),
        "ObservedCorrect": scores.get("ObservedCorrect"),
        "Depth90": scores.get("Depth90"),
        "ObservedDepth90": scores.get("ObservedDepth90"),
    }


def validate_results(path: Path) -> dict[str, Any]:
    try:
        result = read_json(path)
    except Exception as exc:
        return {"valid": False, "issues": [str(exc)]}
    issues: list[str] = []
    required = [
        "schema_version",
        "benchmark_version",
        "run_id",
        "scores",
        "selection",
        "cases",
        "unsupported",
    ]
    for key in required:
        if key not in result:
            issues.append(f"missing {key}")
    if result.get("schema_version") != "osbench.results.v1":
        issues.append("unsupported schema_version")
    requested = result.get("selection", {}).get("requested_cases")
    if isinstance(requested, int) and requested != len(result.get("cases", [])) + len(
        result.get("unsupported", [])
    ):
        issues.append("case accounting mismatch")
    case_ids = [item.get("case_id") for item in result.get("cases", [])]
    if len(case_ids) != len(set(case_ids)):
        issues.append("duplicate evaluated case_id")
    return {
        "valid": not issues,
        "issues": issues,
        "summary": summarize(path) if not issues else None,
    }


def merge_results(paths: list[Path], output: Path | None = None) -> dict[str, Any]:
    documents = [read_json(path) for path in paths]
    if not documents:
        raise ValueError("no result files")
    benchmark_versions = {item.get("benchmark_version") for item in documents}
    if len(benchmark_versions) != 1:
        raise ValueError(f"incompatible benchmark versions: {benchmark_versions}")
    base = documents[0].copy()
    base["cases"] = [case for document in documents for case in document.get("cases", [])]
    base["unsupported"] = [
        case for document in documents for case in document.get("unsupported", [])
    ]
    base["merged_from"] = [str(path) for path in paths]
    base["run_id"] = f"merged-{int(time.time())}"
    base["selection"] = dict(base.get("selection", {}))
    base["selection"].update(
        {
            "requested_cases": len(base["cases"]) + len(base["unsupported"]),
            "evaluated_cases": len(base["cases"]),
            "unsupported_cases": len(base["unsupported"]),
            "complete_shard_set": True,
        }
    )
    from .contracts import contracts_by_id
    from .oracle import aggregate_contract_results
    from .scoring import score_results

    profile = base.get("host", {}).get("profile", "local") or "local"
    base["scores"] = score_results(base["cases"], contracts_by_id(), profile=profile)
    base["contracts"] = aggregate_contract_results(base["cases"])
    output = output or repo_root() / "results" / "merged.json"
    write_json(output, base)
    base["output"] = str(output)
    return base
