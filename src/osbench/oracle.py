from __future__ import annotations

import copy
import hashlib
import os
import platform
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .comparators import compare
from .constants import BENCHMARK_VERSION, REFERENCE_ID
from .contracts import contract_corpus_sha256, contracts_by_id, validate_contracts
from .dataset import build_dataset
from .normalization import normalize_observation
from .paths import repo_root
from .scoring import score_results
from .trajectory import result_metrics
from .targets import LocalTarget, QemuTarget, Target
from .util import jsonl_load, read_json, sha256_file, sha256_value, stable_json, write_json


def _target(specification: str) -> Target:
    if specification == "reference":
        image = repo_root() / "artifacts" / "reference" / "debian-13.6-amd64.qcow2"
        mode = os.environ.get("OSBENCH_REFERENCE_MODE", "qemu").lower()
        if mode == "local":
            return LocalTarget(name="reference-host-fallback")
        if image.exists():
            return QemuTarget(image)
        if mode == "auto":
            return LocalTarget(name="reference-host-fallback")
        raise FileNotFoundError(
            f"Pinned reference image is missing: {image}. Run `osbench reference build`, "
            "or set OSBENCH_REFERENCE_MODE=local explicitly for host-harness validation."
        )
    path = Path(specification).expanduser().resolve()
    if path.exists():
        return QemuTarget(path)
    raise FileNotFoundError(f"Unknown target or missing image: {specification}")


def _close(target: Target) -> None:
    close = getattr(target, "close", None)
    if callable(close):
        close()


def public_cases_path() -> Path:
    return repo_root() / "dataset" / "public" / "v0.1" / "cases.jsonl"


def load_public_cases() -> list[dict[str, Any]]:
    path = public_cases_path()
    if not path.exists():
        build_dataset(profile="public", seed=1, cases_per_contract=10)
    return jsonl_load(path)


def _verify_public_dataset(
    *,
    corpus: list[dict[str, Any]],
    dataset_file_sha256: str,
    contract_corpus_sha256: str,
) -> None:
    manifest_path = repo_root() / "dataset" / "manifests" / "v0.1-public.json"
    if not manifest_path.exists():
        raise ValueError(
            "Public dataset manifest is missing; run `osbench dataset build --profile public`."
        )
    manifest = read_json(manifest_path)
    mismatches: list[str] = []
    if int(manifest.get("case_count", -1)) != len(corpus):
        mismatches.append(
            f"case_count expected {manifest.get('case_count')} observed {len(corpus)}"
        )
    if manifest.get("cases_sha256") != dataset_file_sha256:
        mismatches.append(
            f"cases_sha256 expected {manifest.get('cases_sha256')} observed {dataset_file_sha256}"
        )
    if manifest.get("contract_corpus_sha256") != contract_corpus_sha256:
        mismatches.append(
            "contract_corpus_sha256 expected "
            f"{manifest.get('contract_corpus_sha256')} observed {contract_corpus_sha256}"
        )
    if mismatches:
        raise ValueError(
            "Public dataset and manifest are out of sync: "
            + "; ".join(mismatches)
            + ". Rebuild with `osbench dataset build --profile public --seed 1 "
            "--cases-per-contract 10 --check-determinism`."
        )


def _case_shard(case_id: str, shard_count: int) -> int:
    digest = hashlib.sha256(case_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % shard_count


def select_cases(
    cases: Iterable[dict[str, Any]],
    *,
    one_per_contract: bool = False,
    max_cases: int | None = None,
    shard_count: int = 1,
    shard_index: int = 0,
) -> list[dict[str, Any]]:
    """Select a stable, non-overlapping slice of the case corpus."""

    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard_index must satisfy 0 <= shard_index < shard_count")
    if max_cases is not None and max_cases < 1:
        raise ValueError("max_cases must be at least 1")

    corpus = list(cases)
    if one_per_contract:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for case in corpus:
            grouped.setdefault(str(case["contract"]), []).append(case)

        # Prefer a representative that can share an already-booted clean QEMU
        # snapshot. Every Contract still receives one deterministic public case,
        # while reference self-tests avoid hundreds of redundant guest boots.
        # Lifecycle orchestrators retain their own explicit overlay/reboot logic.
        corpus = [
            min(
                group,
                key=lambda case: (
                    bool(case.get("setup", {}).get("clean_snapshot", True)),
                    str(case.get("case_family", "")),
                    str(case["case_id"]),
                ),
            )
            for _, group in sorted(grouped.items())
        ]

    selected: list[dict[str, Any]] = []
    for case in corpus:
        if _case_shard(str(case["case_id"]), shard_count) != shard_index:
            continue
        selected.append(case)
        if max_cases is not None and len(selected) >= max_cases:
            break
    return selected


def aggregate_contract_results(
    case_results: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in case_results:
        grouped[str(result["contract"])].append(result)

    aggregates: dict[str, dict[str, Any]] = {}
    for contract_id, results in sorted(grouped.items()):
        passed_count = sum(bool(result.get("passed")) for result in results)
        aggregates[contract_id] = {
            "passed": passed_count == len(results),
            "pass_rate": passed_count / len(results),
            "case_count": len(results),
            "failed_cases": [
                str(result["case_id"]) for result in results if not bool(result.get("passed"))
            ],
        }
    return aggregates


def _compare_observations(
    reference_observation: dict[str, Any],
    candidate_observation: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[bool, Any | None]:
    """Fail closed on execution failures, then compare normalized observations."""

    reference_status = reference_observation.get("status")
    if reference_status != "ok":
        return False, {
            "kind": "invalid_reference_observation",
            "reference_status": reference_status,
            "reference_stderr": reference_observation.get("stderr", ""),
        }
    candidate_status = candidate_observation.get("status")
    if candidate_status != "ok":
        return False, {
            "kind": "invalid_candidate_observation",
            "candidate_status": candidate_status,
            "candidate_stderr": candidate_observation.get("stderr", ""),
        }

    normalized_reference = normalize_observation(reference_observation, contract)
    normalized_candidate = normalize_observation(candidate_observation, contract)
    return compare(normalized_reference, normalized_candidate, contract["equivalence"])


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(stable_json(row))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _progress_paths(run_dir: Path, root: Path) -> dict[str, str]:
    return {
        "directory": _relative(run_dir, root),
        "state": _relative(run_dir / "run.state.json", root),
        "journal": _relative(run_dir / "run.journal.jsonl", root),
        "reference_jsonl": _relative(run_dir / "reference.progress.jsonl", root),
        "candidate_jsonl": _relative(run_dir / "candidate.progress.jsonl", root),
        "partial_result": _relative(run_dir / "partial.result.json", root),
    }


def _selection_document(
    *,
    corpus_cases: int,
    selected_cases: int,
    evaluated_cases: int,
    unsupported_cases: int,
    one_per_contract: bool,
    max_cases: int | None,
    shard_count: int,
    shard_index: int,
    reuse_identical_observations: bool,
    dataset_sha256: str,
    dataset_file_sha256: str | None,
    contract_corpus_sha256: str,
) -> dict[str, Any]:
    return {
        "corpus_cases": corpus_cases,
        "requested_cases": selected_cases,
        "evaluated_cases": evaluated_cases,
        "unsupported_cases": unsupported_cases,
        "one_per_contract": one_per_contract,
        "max_cases": max_cases,
        "shard_count": shard_count,
        "shard_index": shard_index,
        "complete_shard_set": shard_count == 1,
        "reused_identical_observations": reuse_identical_observations,
        # Hash the parsed corpus as the authoritative execution identity. This detects
        # a dataset rewrite between independently launched shards even if the path and
        # benchmark version remain unchanged.
        "dataset_sha256": dataset_sha256,
        "dataset_file_sha256": dataset_file_sha256,
        "contract_corpus_sha256": contract_corpus_sha256,
    }


def evaluate(
    *,
    target_spec: str,
    reference_spec: str = "reference",
    max_cases: int | None = None,
    one_per_contract: bool = False,
    output: Path | None = None,
    shard_count: int = 1,
    shard_index: int = 0,
    progress_every: int | None = None,
) -> dict[str, Any]:
    started_ns = time.monotonic_ns()
    started_at_unix = int(time.time())
    validation = validate_contracts()
    if not validation.valid:
        raise ValueError("Contract corpus is invalid")
    contracts = contracts_by_id(validation.contracts)
    corpus = load_public_cases()
    dataset_sha256 = sha256_value(corpus)
    dataset_path = public_cases_path()
    dataset_file_sha256 = sha256_file(dataset_path)
    contract_corpus_digest = contract_corpus_sha256()
    _verify_public_dataset(
        corpus=corpus,
        dataset_file_sha256=dataset_file_sha256,
        contract_corpus_sha256=contract_corpus_digest,
    )
    selected = select_cases(
        corpus,
        one_per_contract=one_per_contract,
        max_cases=max_cases,
        shard_count=shard_count,
        shard_index=shard_index,
    )

    reference: Target | None = None
    candidate: Target | None = None
    run_id = f"eval-{int(time.time())}-{uuid.uuid4().hex[:10]}"
    root = repo_root()
    run_dir = root / "artifacts" / "oracle" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    progress = _progress_paths(run_dir, root)
    state_path = run_dir / "run.state.json"
    journal_path = run_dir / "run.journal.jsonl"
    reference_progress_path = run_dir / "reference.progress.jsonl"
    candidate_progress_path = run_dir / "candidate.progress.jsonl"
    partial_path = run_dir / "partial.result.json"
    reference_raw_path = run_dir / "reference.raw.json"
    candidate_raw_path = run_dir / "candidate.raw.json"
    for path in (journal_path, reference_progress_path, candidate_progress_path):
        path.touch()

    profile = os.environ.get("OSBENCH_PROFILE", "macos_tcg")
    reference_name = reference_spec
    candidate_name = target_spec
    reuse_identical_observations = False
    case_results: list[dict[str, Any]] = []
    unsupported: list[dict[str, str]] = []
    raw_reference: dict[str, Any] = {}
    raw_candidate: dict[str, Any] = {}
    position = 0
    current_case_id: str | None = None
    oracle_queries = 0
    checkpoint_every = max(
        1, int(os.environ.get("OSBENCH_PROGRESS_CHECKPOINT_EVERY", "25"))
    )

    def selection() -> dict[str, Any]:
        return _selection_document(
            corpus_cases=len(corpus),
            selected_cases=len(selected),
            evaluated_cases=len(case_results),
            unsupported_cases=len(unsupported),
            one_per_contract=one_per_contract,
            max_cases=max_cases,
            shard_count=shard_count,
            shard_index=shard_index,
            reuse_identical_observations=reuse_identical_observations,
            dataset_sha256=dataset_sha256,
            dataset_file_sha256=dataset_file_sha256,
            contract_corpus_sha256=contract_corpus_digest,
        )

    def persist(
        status: str,
        *,
        error: BaseException | None = None,
        checkpoint: bool = False,
    ) -> None:
        state: dict[str, Any] = {
            "schema_version": "osbench.run_state.v1",
            "benchmark_version": BENCHMARK_VERSION,
            "run_id": run_id,
            "status": status,
            "updated_at_unix_ns": time.time_ns(),
            "progress": {
                "position": position,
                "total": len(selected),
                "current_case_id": current_case_id,
                "evaluated_cases": len(case_results),
                "unsupported_cases": len(unsupported),
            },
        }
        partial: dict[str, Any] = {
            "schema_version": "osbench.partial_results.v1",
            "benchmark_version": BENCHMARK_VERSION,
            "reference_id": REFERENCE_ID,
            "run_id": run_id,
            "started_at_unix": started_at_unix,
            "status": status,
            "host": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "profile": profile,
            },
            "reference_target": reference_name,
            "candidate_target": candidate_name,
            "selection": selection(),
            "progress": {
                "position": position,
                "total": len(selected),
                "current_case_id": current_case_id,
            },
            "contracts": aggregate_contract_results(case_results),
            "cases": case_results,
            "unsupported": unsupported,
            "artifacts": progress,
        }
        if error is not None:
            error_document = {"type": type(error).__name__, "message": str(error)}
            state["error"] = error_document
            partial["error"] = error_document
        write_json(state_path, state)
        if checkpoint or error is not None or position % checkpoint_every == 0:
            write_json(partial_path, partial)
            write_json(reference_raw_path, raw_reference)
            write_json(candidate_raw_path, raw_candidate)

    _append_jsonl(
        journal_path,
        {
            "event": "run_started",
            "run_id": run_id,
            "timestamp_unix_ns": time.time_ns(),
            "selected_cases": len(selected),
            "shard_count": shard_count,
            "shard_index": shard_index,
            "dataset_sha256": dataset_sha256,
            "dataset_file_sha256": dataset_file_sha256,
            "contract_corpus_sha256": contract_corpus_digest,
        },
    )
    persist("starting", checkpoint=True)

    try:
        reference = _target(reference_spec)
        candidate = _target(target_spec)
        reference_name = getattr(reference, "name", reference_spec)
        candidate_name = getattr(candidate, "name", target_spec)
        reuse_identical_observations = (
            target_spec == reference_spec
            and isinstance(reference, LocalTarget)
            and isinstance(candidate, LocalTarget)
        )
        persist("running")

        for position, case in enumerate(selected, start=1):
            current_case_id = str(case["case_id"])
            _append_jsonl(
                journal_path,
                {
                    "event": "case_started",
                    "run_id": run_id,
                    "timestamp_unix_ns": time.time_ns(),
                    "position": position,
                    "case_id": current_case_id,
                    "contract": case["contract"],
                    "probe": case.get("generator", {}).get("probe"),
                },
            )
            persist("running")

            unsupported_reason: str | None = None
            if not reference.supports(case):
                unsupported_reason = "reference transport unsupported"
            elif not candidate.supports(case):
                unsupported_reason = "candidate transport unsupported"
            if unsupported_reason is not None:
                unsupported.append({"case_id": current_case_id, "reason": unsupported_reason})
                _append_jsonl(
                    journal_path,
                    {
                        "event": "case_unsupported",
                        "run_id": run_id,
                        "timestamp_unix_ns": time.time_ns(),
                        "position": position,
                        "case_id": current_case_id,
                        "reason": unsupported_reason,
                    },
                )
                persist("running")
                continue

            contract = contracts[str(case["contract"])]
            reference_observation = reference.execute(case)
            oracle_queries += 1
            raw_reference[current_case_id] = reference_observation
            _append_jsonl(
                reference_progress_path,
                {
                    "case_id": current_case_id,
                    "contract": case["contract"],
                    "position": position,
                    "observation": reference_observation,
                },
            )
            _append_jsonl(
                journal_path,
                {
                    "event": "reference_observed",
                    "run_id": run_id,
                    "timestamp_unix_ns": time.time_ns(),
                    "position": position,
                    "case_id": current_case_id,
                    "status": reference_observation.get("status"),
                },
            )
            persist("running")

            candidate_observation = (
                copy.deepcopy(reference_observation)
                if reuse_identical_observations
                else candidate.execute(case)
            )
            if not reuse_identical_observations:
                oracle_queries += 1
            raw_candidate[current_case_id] = candidate_observation
            _append_jsonl(
                candidate_progress_path,
                {
                    "case_id": current_case_id,
                    "contract": case["contract"],
                    "position": position,
                    "observation": candidate_observation,
                },
            )
            _append_jsonl(
                journal_path,
                {
                    "event": "candidate_observed",
                    "run_id": run_id,
                    "timestamp_unix_ns": time.time_ns(),
                    "position": position,
                    "case_id": current_case_id,
                    "status": candidate_observation.get("status"),
                    "reused_reference": reuse_identical_observations,
                },
            )

            passed, difference = _compare_observations(
                reference_observation, candidate_observation, contract
            )
            case_result: dict[str, Any] = {
                "case_id": current_case_id,
                "contract": case["contract"],
                "domain": case["domain"],
                "level": case["level"],
                "family": case["family"],
                "passed": passed,
                "difference": difference,
                "reference_status": reference_observation.get("status"),
                "candidate_status": candidate_observation.get("status"),
            }
            reference_duration = reference_observation.get("duration_ns")
            candidate_duration = candidate_observation.get("duration_ns")
            if (
                isinstance(reference_duration, (int, float))
                and isinstance(candidate_duration, (int, float))
                and reference_duration > 0
            ):
                case_result["performance_ratio"] = candidate_duration / reference_duration
            case_results.append(case_result)
            _append_jsonl(
                journal_path,
                {
                    "event": "case_completed",
                    "run_id": run_id,
                    "timestamp_unix_ns": time.time_ns(),
                    "position": position,
                    "case_id": current_case_id,
                    "passed": passed,
                },
            )
            persist("running")

            if progress_every and position % progress_every == 0:
                sys.stderr.write(
                    stable_json(
                        {
                            "event": "evaluation_progress",
                            "run_id": run_id,
                            "position": position,
                            "total": len(selected),
                            "evaluated": len(case_results),
                            "unsupported": len(unsupported),
                            "case_id": current_case_id,
                        }
                    )
                    + "\n"
                )
                sys.stderr.flush()
    except BaseException as exc:
        _append_jsonl(
            journal_path,
            {
                "event": "run_failed",
                "run_id": run_id,
                "timestamp_unix_ns": time.time_ns(),
                "position": position,
                "case_id": current_case_id,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        persist("failed", error=exc, checkpoint=True)
        raise
    finally:
        if reference is not None:
            _close(reference)
        if candidate is not None:
            _close(candidate)

    current_case_id = None
    contract_aggregates = aggregate_contract_results(case_results)
    scores = score_results(case_results, contracts, profile=profile)
    output = output or root / "results" / f"{run_id}.json"
    result_document = {
        "schema_version": "osbench.results.v1",
        "benchmark_version": BENCHMARK_VERSION,
        "reference_id": REFERENCE_ID,
        "run_id": run_id,
        "started_at_unix": started_at_unix,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "profile": profile,
        },
        "reference_target": reference_name,
        "candidate_target": candidate_name,
        "selection": selection(),
        "scores": scores,
        "trajectory": result_metrics(
            started_ns=started_ns,
            contract_results=contract_aggregates,
            evaluated_cases=len(case_results),
            oracle_queries=oracle_queries,
            target_spec=target_spec,
        ),
        "contracts": contract_aggregates,
        "cases": case_results,
        "unsupported": unsupported,
        "raw_observations": _relative(run_dir, root),
        "progress": progress,
    }
    write_json(output, result_document)
    _append_jsonl(
        journal_path,
        {
            "event": "run_completed",
            "run_id": run_id,
            "timestamp_unix_ns": time.time_ns(),
            "position": position,
            "evaluated_cases": len(case_results),
            "unsupported_cases": len(unsupported),
            "output": str(output),
        },
    )
    persist("completed", checkpoint=True)
    result_document["output"] = str(output)
    return result_document


def selftest() -> dict[str, Any]:
    return evaluate(
        target_spec="reference",
        reference_spec="reference",
        one_per_contract=True,
        output=repo_root() / "results" / "oracle-selftest.json",
    )
