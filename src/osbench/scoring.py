from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .constants import LEVELS
from .paths import repo_root
from .util import read_yaml


def _geometric(values: list[tuple[float, float]], epsilon: float) -> float:
    if not values:
        return 0.0
    weight_sum = sum(weight for _, weight in values)
    if weight_sum <= 0:
        return 0.0
    log_sum = sum(weight * math.log(max(value, epsilon)) for value, weight in values)
    return math.exp(log_sum / weight_sum)


def _depth(
    *,
    contract_scores: dict[str, float],
    contracts: dict[str, dict[str, Any]],
    threshold: float,
    observed_only: bool,
) -> str | None:
    depth: str | None = None
    cumulative: list[bool] = []
    for level in LEVELS:
        ids = sorted(
            contract_id
            for contract_id, contract in contracts.items()
            if contract["level"] == level
            and (not observed_only or contract_id in contract_scores)
        )
        # Depth is a contiguous capability prefix. A candidate cannot recover a
        # deeper level by accumulating many later easy passes after missing an
        # earlier foundational surface. Observed depth likewise requires at least
        # one observation at every level in the reported prefix.
        if not ids:
            break
        cumulative.extend(contract_scores.get(contract_id, 0.0) >= 1.0 for contract_id in ids)
        if sum(cumulative) / len(cumulative) < threshold:
            break
        depth = level
    return depth


def score_results(
    case_results: list[dict[str, Any]], contracts: dict[str, dict[str, Any]], *, profile: str
) -> dict[str, Any]:
    """Score complete benchmark capability coverage and the observed execution surface.

    Contract families, rather than individual generated cases, are the scoring unit. An
    unevaluated Contract contributes zero to the authoritative score. This prevents a
    partial transport, a narrow public slice, or an unsupported subsystem from reporting
    a perfect benchmark score. Evaluated-only diagnostics remain available as
    ``ObservedCorrect`` and ``ObservedDepth90`` for harness self-tests.
    """

    configuration = read_yaml(repo_root() / "config" / "benchmark.yaml")
    epsilon = float(configuration["scoring"]["geometric_epsilon"])
    threshold = float(configuration["scoring"]["depth_threshold"])
    weights = configuration["level_weights"]

    by_contract: defaultdict[str, list[bool]] = defaultdict(list)
    workload_cases: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in case_results:
        contract_id = str(result["contract"])
        if contract_id not in contracts:
            raise KeyError(f"Result references unknown Contract: {contract_id}")
        by_contract[contract_id].append(bool(result["passed"]))
        if contracts[contract_id]["level"] in {"real_workloads", "full_reconstruction"}:
            workload_cases[contract_id].append(result)

    contract_scores = {
        contract_id: sum(results) / len(results) for contract_id, results in by_contract.items()
    }
    contract_passed = {
        contract_id: score >= 1.0 for contract_id, score in contract_scores.items()
    }

    contract_ids_by_level = {
        level: sorted(
            contract_id
            for contract_id, contract in contracts.items()
            if contract["level"] == level
        )
        for level in LEVELS
    }
    level_scores: dict[str, float] = {}
    observed_level_scores: dict[str, float | None] = {}
    level_coverage: dict[str, float] = {}
    for level in LEVELS:
        ids = contract_ids_by_level[level]
        observed = [contract_scores[item] for item in ids if item in contract_scores]
        level_scores[level] = (
            sum(contract_scores.get(item, 0.0) for item in ids) / len(ids) if ids else 0.0
        )
        observed_level_scores[level] = sum(observed) / len(observed) if observed else None
        level_coverage[level] = (
            sum(item in contract_scores for item in ids) / len(ids) if ids else 0.0
        )

    boot_ids = contract_ids_by_level["boot"]
    boot_gate = (
        1.0
        if boot_ids
        and all(item in contract_scores and contract_passed[item] for item in boot_ids)
        else 0.0
    )
    observed_boot_ids = [item for item in boot_ids if item in contract_scores]
    observed_boot_gate = (
        1.0
        if observed_boot_ids and all(contract_passed[item] for item in observed_boot_ids)
        else 0.0
    )

    weighted_levels = [
        (float(level_scores[level]), float(weights[level])) for level in LEVELS
    ]
    observed_weighted_levels = [
        (float(observed_level_scores[level]), float(weights[level]))
        for level in LEVELS
        if observed_level_scores[level] is not None
    ]
    oscorrect = boot_gate * _geometric(weighted_levels, epsilon)
    observed_correct = observed_boot_gate * _geometric(observed_weighted_levels, epsilon)

    depth90 = _depth(
        contract_scores=contract_scores,
        contracts=contracts,
        threshold=threshold,
        observed_only=False,
    )
    observed_depth90 = _depth(
        contract_scores=contract_scores,
        contracts=contracts,
        threshold=threshold,
        observed_only=True,
    )

    native: dict[str, float | None] = {}
    official_performance = bool(
        configuration["profiles"].get(profile, {}).get("official_performance", False)
    )
    workload_ids = sorted(
        contract_id
        for contract_id, contract in contracts.items()
        if contract["level"] in {"real_workloads", "full_reconstruction"}
    )
    for native_threshold in configuration["scoring"]["native_thresholds"]:
        key = f"Native_{native_threshold:g}"
        if not official_performance:
            native[key] = None
            continue
        if not workload_ids:
            native[key] = 0.0
            continue
        qualifying = 0
        for contract_id in workload_ids:
            results = workload_cases.get(contract_id, [])
            if not results or not all(bool(result.get("passed")) for result in results):
                continue
            ratios = [result.get("performance_ratio") for result in results]
            if all(
                isinstance(ratio, (int, float))
                and float(ratio) <= float(native_threshold)
                for ratio in ratios
            ):
                qualifying += 1
        native[key] = qualifying / len(workload_ids)

    return {
        "OSCorrect": oscorrect,
        "ObservedCorrect": observed_correct,
        "Depth90": depth90,
        "ObservedDepth90": observed_depth90,
        **native,
        "boot_gate": boot_gate,
        "observed_boot_gate": observed_boot_gate,
        "level_scores": level_scores,
        "observed_level_scores": observed_level_scores,
        "level_coverage": level_coverage,
        "contract_scores": contract_scores,
        "evaluated_contracts": len(contract_scores),
        "passed_contracts": sum(contract_passed.values()),
        "corpus_contracts": len(contracts),
        "contract_coverage": len(contract_scores) / len(contracts) if contracts else 0.0,
        "evaluated_cases": len(case_results),
        "official_performance_profile": official_performance,
        "native_workload_contracts": len(workload_ids),
    }
