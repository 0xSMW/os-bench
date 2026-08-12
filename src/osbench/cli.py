from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer

from .contracts import validate_contracts
from .dataset import build_dataset, check_determinism, validate_dataset
from .doctor import doctor as run_doctor
from .full_selftest import run_full_local_selftest
from .graph import (
    contracts_for_workload,
    frontier,
    prerequisites,
    unlocked_by,
    workloads_for,
    write_graph_outputs,
)
from .oracle import evaluate, selftest
from .payload import build_payload, stage_payload, validate_payload_tree
from .perturbations import perturbation_selftest
from .reference import (
    boot_reference,
    build_reference,
    calibrate_unsynced_outcomes,
    export_rootfs,
    inventory_reference,
    preflight_reference,
    realize_lock,
)
from .results import merge_results, summarize, validate_results
from .source_lock import synchronize_source_lock
from .tracing import trace_workload
from .trajectory import TrajectoryRecorder, summarize_trajectory

app = typer.Typer(help="OSBench: behavioral evaluation for reconstructing Linux-compatible operating systems", no_args_is_help=True)
contracts_app = typer.Typer(help="Validate and inspect Contract definitions", no_args_is_help=True)
dataset_app = typer.Typer(help="Build deterministic evaluation datasets", no_args_is_help=True)
graph_app = typer.Typer(help="Build and query the capability DAG", no_args_is_help=True)
reference_app = typer.Typer(help="Build, boot, inspect, and lock the reference distribution", no_args_is_help=True)
oracle_app = typer.Typer(help="Run differential-oracle operations", no_args_is_help=True)
results_app = typer.Typer(help="Inspect benchmark result files", no_args_is_help=True)
trace_app = typer.Typer(help="Trace reference workloads", no_args_is_help=True)
trajectory_app = typer.Typer(help="Record and summarize AI build trajectories", no_args_is_help=True)
payload_app = typer.Typer(help="Build evaluator payload media", no_args_is_help=True)

app.add_typer(contracts_app, name="contracts")
app.add_typer(dataset_app, name="dataset")
app.add_typer(graph_app, name="graph")
app.add_typer(reference_app, name="reference")
app.add_typer(oracle_app, name="oracle")
app.add_typer(results_app, name="results")
app.add_typer(trace_app, name="trace")
app.add_typer(trajectory_app, name="trajectory")
app.add_typer(payload_app, name="payload")


def emit(value: object) -> None:
    typer.echo(json.dumps(value, sort_keys=True, indent=2, default=str))


@app.command()
def doctor(strict: bool = typer.Option(False, help="Exit nonzero when optional VM tools are missing")) -> None:
    report = run_doctor()
    emit(report)
    if report["contract_issues"]:
        raise typer.Exit(1)
    if strict and (not report["tools"].get("qemu-system-x86_64") or not report["firmware"]):
        raise typer.Exit(1)


@contracts_app.command("validate")
def contracts_validate() -> None:
    report = validate_contracts()
    output = {"valid": report.valid, "stats": report.stats(), "issues": [issue.__dict__ for issue in report.issues]}
    emit(output)
    if not report.valid:
        raise typer.Exit(1)


@app.command("contracts-validate")
def contracts_validate_alias() -> None:
    contracts_validate()


@dataset_app.command("build")
def dataset_build(
    profile: str = typer.Option("public"),
    seed: int = typer.Option(1),
    cases_per_contract: int = typer.Option(10, min=1, max=1000),
    determinism: bool = typer.Option(False, "--check-determinism"),
) -> None:
    manifest = build_dataset(profile=profile, seed=seed, cases_per_contract=cases_per_contract)
    if determinism:
        manifest["deterministic"] = check_determinism(profile=profile, seed=seed, cases_per_contract=cases_per_contract)
        if not manifest["deterministic"]:
            emit(manifest)
            raise typer.Exit(1)
    emit(manifest)


@dataset_app.command("validate")
def dataset_validate(path: Optional[Path] = typer.Option(None)) -> None:
    report = validate_dataset(path)
    emit(report)
    if not report["valid"]:
        raise typer.Exit(1)


@app.command("dataset-build")
def dataset_build_alias(
    profile: str = typer.Option("public"), seed: int = typer.Option(1), cases_per_contract: int = typer.Option(10)
) -> None:
    emit(build_dataset(profile=profile, seed=seed, cases_per_contract=cases_per_contract))


@payload_app.command("stage")
def payload_stage(output: Optional[Path] = typer.Option(None)) -> None:
    emit(stage_payload(output))


@payload_app.command("validate")
def payload_validate(path: Optional[Path] = typer.Option(None)) -> None:
    report = validate_payload_tree(path)
    emit(report)
    if not report["valid"]:
        raise typer.Exit(1)


@payload_app.command("build")
def payload_build(output: Optional[Path] = typer.Option(None)) -> None:
    emit(build_payload(output))


@app.command("payload-build")
def payload_build_alias(output: Optional[Path] = typer.Option(None)) -> None:
    emit(build_payload(output))


@graph_app.command("build")
def graph_build() -> None:
    emit(write_graph_outputs())


@graph_app.command("prerequisites")
def graph_prerequisites(contract_id: str, direct: bool = typer.Option(False)) -> None:
    emit({"contract": contract_id, "prerequisites": prerequisites(contract_id, transitive=not direct)})


@graph_app.command("unlocked")
def graph_unlocked(contract_id: str, transitive: bool = typer.Option(False)) -> None:
    emit({"contract": contract_id, "unlocked": unlocked_by(contract_id, transitive=transitive)})


@graph_app.command("frontier")
def graph_frontier(results_path: Path) -> None:
    emit({"results": str(results_path), "frontier": frontier(results_path)})


@graph_app.command("workload")
def graph_workload(workload: str) -> None:
    emit({"workload": workload, "contracts": contracts_for_workload(workload)})


@graph_app.command("blocked")
def graph_blocked(contract_id: str) -> None:
    emit({"contract": contract_id, "workloads": workloads_for(contract_id)})


@reference_app.command("build")
def reference_build() -> None:
    emit(build_reference())


@app.command("reference-build")
def reference_build_alias() -> None:
    reference_build()


@reference_app.command("boot")
def reference_boot(profile: Optional[str] = typer.Option(None)) -> None:
    emit(boot_reference(profile=profile))


@app.command("reference-boot")
def reference_boot_alias(profile: Optional[str] = typer.Option(None)) -> None:
    emit(boot_reference(profile=profile))


@reference_app.command("inventory")
def reference_inventory(profile: Optional[str] = typer.Option(None)) -> None:
    emit(inventory_reference(profile=profile))


@app.command("reference-inventory")
def reference_inventory_alias(profile: Optional[str] = typer.Option(None)) -> None:
    emit(inventory_reference(profile=profile))


@reference_app.command("preflight")
def reference_preflight(
    profile: Optional[str] = typer.Option(None),
    verify_hashes: bool = typer.Option(
        False,
        "--verify-hashes",
        help="Hash present artifacts, including the multi-gigabyte Debian ISO",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit nonzero unless every artifact is present and bound to the realized lock",
    ),
) -> None:
    report = preflight_reference(profile=profile, verify_hashes=verify_hashes)
    emit(report)
    if strict and not report["materialization_ready"]:
        raise typer.Exit(1)


@app.command("reference-preflight")
def reference_preflight_alias(
    profile: Optional[str] = typer.Option(None),
    verify_hashes: bool = typer.Option(False, "--verify-hashes"),
    strict: bool = typer.Option(False, "--strict"),
) -> None:
    report = preflight_reference(profile=profile, verify_hashes=verify_hashes)
    emit(report)
    if strict and not report["materialization_ready"]:
        raise typer.Exit(1)


@reference_app.command("calibrate-unsynced")
def reference_calibrate_unsynced(
    trials: int = typer.Option(20, min=2, max=1000),
    profile: Optional[str] = typer.Option(None),
    output: Optional[Path] = typer.Option(None),
    seed: int = typer.Option(73013),
) -> None:
    emit(
        calibrate_unsynced_outcomes(
            trials=trials,
            profile=profile,
            output=output,
            seed=seed,
        )
    )


@app.command("reference-calibrate-unsynced")
def reference_calibrate_unsynced_alias(
    trials: int = typer.Option(20, min=2),
    profile: Optional[str] = typer.Option(None),
    output: Optional[Path] = typer.Option(None),
    seed: int = typer.Option(73013),
) -> None:
    reference_calibrate_unsynced(
        trials=trials,
        profile=profile,
        output=output,
        seed=seed,
    )


@reference_app.command("lock-sources")
def reference_lock_sources(
    check: bool = typer.Option(False, "--check", help="Verify source hashes without changing the lock"),
) -> None:
    report = synchronize_source_lock(check=check)
    emit(report)
    if check and not report["valid"]:
        raise typer.Exit(1)


@reference_app.command("lock-realize")
def reference_lock_realize() -> None:
    emit(realize_lock())


@reference_app.command("export-oci")
def reference_export_oci() -> None:
    emit(export_rootfs())


@oracle_app.command("selftest")
def oracle_selftest() -> None:
    result = selftest()
    emit({"output": result["output"], "scores": result["scores"], "selection": result["selection"]})
    if any(not case["passed"] for case in result["cases"]):
        raise typer.Exit(1)


@oracle_app.command("full-selftest")
def oracle_full_selftest(
    shard_count: int = typer.Option(32, min=1),
    jobs: Optional[int] = typer.Option(None, min=1),
    shard_timeout_seconds: float = typer.Option(300.0, min=1.0),
    progress_every: int = typer.Option(25, min=1),
    worker_max_cases: int = typer.Option(1, min=1),
    output: Optional[Path] = typer.Option(None),
    one_per_contract: bool = typer.Option(
        False,
        "--one-per-contract",
        help="Evaluate one generated case per Contract with independent reference and candidate observations",
    ),
    max_cases_per_shard: Optional[int] = typer.Option(
        None, min=1, hidden=True, help="Test-only cap applied independently to each shard"
    ),
) -> None:
    report = run_full_local_selftest(
        shard_count=shard_count,
        jobs=jobs,
        shard_timeout_seconds=shard_timeout_seconds,
        progress_every=progress_every,
        worker_max_cases=worker_max_cases,
        output=output,
        max_cases_per_shard=max_cases_per_shard,
        one_per_contract=one_per_contract,
    )
    emit(
        {
            "output": report["output"],
            "report": report["report"],
            "scores": report["scores"],
            "selection": report["selection"],
            "elapsed_seconds": report["elapsed_seconds"],
        }
    )
    if not report["passed"]:
        raise typer.Exit(1)


@app.command("full-selftest")
def oracle_full_selftest_alias(
    shard_count: int = typer.Option(32, min=1),
    jobs: Optional[int] = typer.Option(None, min=1),
    shard_timeout_seconds: float = typer.Option(300.0, min=1.0),
    progress_every: int = typer.Option(25, min=1),
    worker_max_cases: int = typer.Option(1, min=1),
    output: Optional[Path] = typer.Option(None),
    one_per_contract: bool = typer.Option(False, "--one-per-contract"),
) -> None:
    report = run_full_local_selftest(
        shard_count=shard_count,
        jobs=jobs,
        shard_timeout_seconds=shard_timeout_seconds,
        progress_every=progress_every,
        worker_max_cases=worker_max_cases,
        output=output,
        one_per_contract=one_per_contract,
    )
    emit(
        {
            "output": report["output"],
            "report": report["report"],
            "scores": report["scores"],
            "selection": report["selection"],
            "elapsed_seconds": report["elapsed_seconds"],
        }
    )
    if not report["passed"]:
        raise typer.Exit(1)


@oracle_app.command("perturbation-selftest")
def oracle_perturbation_selftest(limit: int = typer.Option(12, min=1, max=100)) -> None:
    report = perturbation_selftest(limit=limit)
    emit(report)
    if not report["passed"]:
        raise typer.Exit(1)


@app.command("oracle-selftest")
def oracle_selftest_alias() -> None:
    oracle_selftest()


@app.command("eval")
def eval_command(
    target: str = typer.Option(..., "--target"),
    reference: str = typer.Option("reference", "--reference"),
    max_cases: Optional[int] = typer.Option(None, min=1),
    one_per_contract: bool = typer.Option(False),
    output: Optional[Path] = typer.Option(None),
    shard_count: int = typer.Option(1, min=1),
    shard_index: int = typer.Option(0, min=0),
    progress_every: Optional[int] = typer.Option(None, min=1),
) -> None:
    result = evaluate(
        target_spec=target,
        reference_spec=reference,
        max_cases=max_cases,
        one_per_contract=one_per_contract,
        output=output,
        shard_count=shard_count,
        shard_index=shard_index,
        progress_every=progress_every,
    )
    emit({"output": result["output"], "scores": result["scores"], "selection": result["selection"]})
    if any(not case["passed"] for case in result["cases"]):
        raise typer.Exit(1)


@app.command("smoke")
def smoke() -> None:
    result = evaluate(
        target_spec="reference",
        reference_spec="reference",
        one_per_contract=True,
        output=Path("results/smoke.json"),
    )
    emit({"output": result["output"], "scores": result["scores"], "selection": result["selection"]})
    if any(not case["passed"] for case in result["cases"]):
        raise typer.Exit(1)


@results_app.command("summarize")
def results_summarize(results_path: Path) -> None:
    emit(summarize(results_path))


@results_app.command("validate")
def results_validate(results_path: Path) -> None:
    report = validate_results(results_path)
    emit(report)
    if not report["valid"]:
        raise typer.Exit(1)


@results_app.command("merge")
def results_merge(
    paths: list[Path] = typer.Argument(..., help="Shard result files to merge"),
    output: Optional[Path] = typer.Option(None),
) -> None:
    document = merge_results(paths, output=output)
    emit({
        "output": document["output"],
        "scores": document["scores"],
        "selection": document["selection"],
    })


@trace_app.command("workload")
def trace_workload_command(
    name: str, profile: Optional[str] = typer.Option(None)
) -> None:
    emit(trace_workload(name, profile=profile))


@trajectory_app.command("init")
def trajectory_init(
    path: Optional[Path] = typer.Option(None), run_id: Optional[str] = typer.Option(None)
) -> None:
    recorder = TrajectoryRecorder.create(path=path, run_id=run_id)
    event = recorder.append("run_started")
    emit({"path": str(recorder.path), "run_id": recorder.run_id, "event": event})


@trajectory_app.command("record")
def trajectory_record(
    path: Path, event: str, contracts_passed: Optional[int] = typer.Option(None),
    level: Optional[str] = typer.Option(None), tokens: Optional[int] = typer.Option(None),
) -> None:
    recorder = TrajectoryRecorder.create(path=path, run_id=path.stem)
    values = {
        key: value
        for key, value in {
            "contracts_passed": contracts_passed, "level": level, "tokens": tokens
        }.items()
        if value is not None
    }
    emit(recorder.append(event, **values))


@trajectory_app.command("summarize")
def trajectory_summarize(path: Path) -> None:
    emit(summarize_trajectory(path))


@app.command("shell", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def shell(ctx: typer.Context) -> None:
    command = ["/bin/bash", *ctx.args]
    os.execvp(command[0], command)


if __name__ == "__main__":
    app()
