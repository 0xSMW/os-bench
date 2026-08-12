from __future__ import annotations

import copy
from collections import Counter
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .constants import BENCHMARK_VERSION, REFERENCE_ID
from .contracts import validate_contracts
from .dataset import generate_cases
from .inventory import collect_reference
from .oci import build_oci_layout
from .paths import repo_root
from .qemu import QemuController, load_profile
from .source_lock import synchronize_source_lock
from .targets import QemuTarget
from .util import read_json, sha256_file, write_json


def _first_version_line(command: list[str]) -> str | None:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    lines = (completed.stdout or completed.stderr).splitlines()
    return lines[0] if lines else None


def build_reference() -> dict[str, Any]:
    root = repo_root()
    script = root / "reference" / "build" / "build_image.sh"
    completed = subprocess.run([str(script)], cwd=root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"reference build failed:\n{completed.stdout}\n{completed.stderr}")
    image = Path(completed.stdout.strip().splitlines()[-1])
    result: dict[str, Any] = {
        "image": str(image),
        "sha256": sha256_file(image),
        "log": "artifacts/reference/install.log",
    }
    installer_manifest = root / "artifacts" / "reference" / "installer" / "manifest.json"
    if installer_manifest.exists():
        result["installer"] = read_json(installer_manifest).get("custom_iso")
    return result


def boot_reference(*, profile: str | None = None) -> dict[str, Any]:
    root = repo_root()
    image = root / "artifacts" / "reference" / "debian-13.6-amd64.qcow2"
    controller = QemuController(profile)
    return controller.boot_check(image)


def inventory_reference(*, profile: str | None = None) -> dict[str, Any]:
    root = repo_root()
    image = root / "artifacts/reference/debian-13.6-amd64.qcow2"
    script = root / "reference/inventory/collect.sh"
    if image.is_file() and shutil.which("virt-copy-out"):
        completed = subprocess.run([str(script), str(image)], cwd=root, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"reference inventory failed:\n{completed.stdout}\n{completed.stderr}")
        output = Path(completed.stdout.strip().splitlines()[-1])
        manifest = read_json(output / "manifest.json")
        return {**manifest, "output": str(output), "profile": profile}
    return collect_reference(profile=profile)


def preflight_reference(
    *,
    profile: str | None = None,
    verify_hashes: bool = False,
) -> dict[str, Any]:
    """Report every prerequisite and artifact needed to materialize the oracle.

    This command is intentionally read-only. It gives local and CI environments a
    deterministic answer about the next missing stage before beginning a multi-hour
    Debian installation under TCG.
    """

    root = repo_root()
    profile_config = load_profile(profile)
    lock = read_json(root / "reference" / "lock.json")
    source_lock = synchronize_source_lock(check=True)
    cache_root = Path(os.environ.get("OSBENCH_CACHE", str(Path.home() / ".cache/osbench")))
    source_iso = cache_root / "reference" / str(lock["source"]["filename"])

    tool_names = [
        "python3",
        "curl",
        "gpgv",
        "sha256sum",
        "xorriso",
        "qemu-system-x86_64",
        "qemu-img",
        "guestfish",
        "virt-copy-out",
        "gcc",
        "x86_64-linux-gnu-gcc",
        "dpkg-deb",
        "make",
    ]
    tools = {name: shutil.which(name) for name in tool_names}
    firmware_code = next(
        (path for path in profile_config.firmware_code_candidates if Path(path).is_file()),
        None,
    )
    firmware_vars = next(
        (path for path in profile_config.firmware_vars_candidates if Path(path).is_file()),
        None,
    )
    keyring = Path("/usr/share/keyrings/debian-role-keys.gpg")

    artifact_paths = {
        "source_iso": source_iso,
        "payload_iso": root / "artifacts/payload/osbench-payload.iso",
        "reference_image": root / "artifacts/reference/debian-13.6-amd64.qcow2",
        "inventory_manifest": root / "artifacts/reference/inventory/manifest.json",
        "rootfs_tar": root / "artifacts/reference/debian-13.6-rootfs.tar",
        "oci_archive": root
        / "artifacts/reference/osbench-reference-13.6-v0.1.oci.tar",
        "calibration": root
        / "reference/oracle"
        / f"unsynced_outcomes.{profile_config.name}.json",
        "realized_lock": root / "artifacts/reference/lock.realized.json",
    }
    artifacts: dict[str, Any] = {}
    for name, path in artifact_paths.items():
        record: dict[str, Any] = {"path": str(path), "present": path.is_file()}
        if path.is_file():
            record["size_bytes"] = path.stat().st_size
            if verify_hashes:
                record["sha256"] = sha256_file(path)
        artifacts[name] = record

    source_iso_valid: bool | None = None
    if source_iso.is_file():
        source_iso_valid = source_iso.stat().st_size == int(lock["source"]["size_bytes"])
        if verify_hashes:
            source_iso_valid = source_iso_valid and (
                artifacts["source_iso"].get("sha256") == lock["source"]["sha256"]
            )

    calibration_ready = False
    calibration_reason = "missing"
    calibration_binding_verified: bool | None = None
    calibration_path = artifact_paths["calibration"]
    image_path = artifact_paths["reference_image"]
    payload_path = artifact_paths["payload_iso"]
    calibration: dict[str, Any] | None = None
    if calibration_path.is_file():
        try:
            candidate = read_json(calibration_path)
        except (OSError, ValueError):
            calibration_reason = "invalid_json"
        else:
            if isinstance(candidate, dict):
                calibration = candidate
            else:
                calibration_reason = "invalid_document"
    if calibration is not None:
        outcomes = calibration.get("outcomes")
        metadata_valid = (
            calibration.get("schema_version") == "osbench.accepted_outcomes.v1"
            and calibration.get("benchmark_version") == BENCHMARK_VERSION
            and calibration.get("reference_id") == REFERENCE_ID
            and calibration.get("profile") == profile_config.name
            and calibration.get("contract") == "persistence.crash.unsynced_bounds"
            and isinstance(outcomes, list)
            and bool(outcomes)
            and all(isinstance(outcome, str) and outcome for outcome in outcomes)
            and isinstance(calibration.get("reference_image_sha256"), str)
            and len(calibration["reference_image_sha256"]) == 64
            and isinstance(calibration.get("payload_sha256"), str)
            and len(calibration["payload_sha256"]) == 64
        )
        artifacts_present = image_path.is_file() and payload_path.is_file()
        if not metadata_valid:
            calibration_reason = "metadata_mismatch"
        elif not artifacts_present:
            calibration_reason = "artifacts_missing"
        elif verify_hashes:
            calibration_binding_verified = (
                calibration.get("reference_image_sha256")
                == artifacts["reference_image"].get("sha256")
                and calibration.get("payload_sha256")
                == artifacts["payload_iso"].get("sha256")
            )
            calibration_ready = calibration_binding_verified
            calibration_reason = (
                "ready" if calibration_ready else "metadata_or_artifact_mismatch"
            )
        else:
            calibration_ready = True
            calibration_reason = "ready_unverified"

    realized_lock_ready = False
    realized_lock_reason = "missing"
    realized_lock_binding_verified: bool | None = None
    realized_path = artifact_paths["realized_lock"]
    realized: dict[str, Any] | None = None
    if realized_path.is_file():
        try:
            candidate = read_json(realized_path)
        except (OSError, ValueError):
            realized_lock_reason = "invalid_json"
        else:
            if isinstance(candidate, dict):
                realized = candidate
            else:
                realized_lock_reason = "invalid_document"
    if realized is not None:
        resolved = realized.get("resolved_from_installed_system")
        source_sections_match = all(
            realized.get(section) == lock.get(section)
            for section in (
                "benchmark_sources",
                "container_build_environment",
                "offline_package_corpus",
                "payload_sources",
                "raw_probe_sources",
                "reference_builder_sources",
                "workload_fixture_sources",
            )
        )
        required_resolved_fields = (
            "image_sha256",
            "package_manifest_sha256",
            "kernel_version",
            "systemd_version",
            "libc_version",
            "payload_sha256",
            "oci_rootfs_sha256",
            "oci_archive_sha256",
            "unsynced_outcome_calibration_sha256",
        )
        resolved_fields_present = (
            isinstance(resolved, dict)
            and all(resolved.get(field) for field in required_resolved_fields)
            and resolved.get("unsynced_outcome_calibration_profile")
            == profile_config.name
        )
        artifacts_present = all(
            artifacts[name]["present"]
            for name in (
                "reference_image",
                "payload_iso",
                "inventory_manifest",
                "rootfs_tar",
                "oci_archive",
                "calibration",
            )
        )
        metadata_valid = (
            realized.get("benchmark_version") == BENCHMARK_VERSION
            and realized.get("reference_id") == REFERENCE_ID
            and realized.get("status") == "materialized"
            and isinstance(resolved, dict)
        )
        structural_ready = bool(
            metadata_valid
            and source_sections_match
            and resolved_fields_present
            and artifacts_present
            and calibration_ready
        )
        if not structural_ready:
            realized_lock_reason = "metadata_source_or_artifact_mismatch"
        elif verify_hashes:
            assert isinstance(resolved, dict)
            realized_lock_binding_verified = (
                resolved.get("image_sha256")
                == artifacts["reference_image"].get("sha256")
                and resolved.get("payload_sha256")
                == artifacts["payload_iso"].get("sha256")
                and resolved.get("oci_rootfs_sha256")
                == artifacts["rootfs_tar"].get("sha256")
                and resolved.get("oci_archive_sha256")
                == artifacts["oci_archive"].get("sha256")
                and resolved.get("unsynced_outcome_calibration_sha256")
                == artifacts["calibration"].get("sha256")
            )
            realized_lock_ready = realized_lock_binding_verified
            realized_lock_reason = (
                "ready" if realized_lock_ready else "artifact_hash_mismatch"
            )
        else:
            realized_lock_ready = True
            realized_lock_reason = "ready_unverified"

    stages = {
        "source_acquisition": {
            "ready": all(tools[name] for name in ("curl", "gpgv", "sha256sum"))
            and keyring.is_file(),
            "missing_tools": [
                name for name in ("curl", "gpgv", "sha256sum") if not tools[name]
            ],
            "debian_role_keyring": str(keyring) if keyring.is_file() else None,
        },
        "payload_build": {
            "ready": all(
                tools[name]
                for name in ("xorriso", "gcc", "x86_64-linux-gnu-gcc", "dpkg-deb", "make")
            ),
            "missing_tools": [
                name
                for name in ("xorriso", "gcc", "x86_64-linux-gnu-gcc", "dpkg-deb", "make")
                if not tools[name]
            ],
        },
        "reference_build": {
            "ready": all(
                tools[name]
                for name in ("xorriso", "qemu-system-x86_64", "qemu-img", "guestfish")
            )
            and firmware_code is not None
            and firmware_vars is not None,
            "missing_tools": [
                name
                for name in ("xorriso", "qemu-system-x86_64", "qemu-img", "guestfish")
                if not tools[name]
            ],
            "firmware_code": firmware_code,
            "firmware_vars": firmware_vars,
        },
        "inventory_and_oci": {
            "ready": bool(tools["guestfish"] and tools["virt-copy-out"]),
            "missing_tools": [
                name for name in ("guestfish", "virt-copy-out") if not tools[name]
            ],
        },
    }

    next_action: str | None
    if not source_lock["valid"]:
        next_action = "osbench reference lock-sources"
    elif realized_lock_ready:
        next_action = None
    elif (
        artifacts["payload_iso"]["present"]
        and artifacts["reference_image"]["present"]
        and artifacts["inventory_manifest"]["present"]
        and artifacts["rootfs_tar"]["present"]
        and artifacts["oci_archive"]["present"]
        and calibration_ready
    ):
        next_action = "osbench reference lock-realize"
    elif (
        not stages["source_acquisition"]["ready"]
        or not stages["payload_build"]["ready"]
        or not stages["reference_build"]["ready"]
        or not stages["inventory_and_oci"]["ready"]
    ):
        next_action = "docker compose build"
    elif source_iso_valid is False:
        next_action = f"remove invalid cached source ISO: {source_iso}"
    elif not artifacts["payload_iso"]["present"]:
        next_action = "osbench payload build"
    elif not artifacts["reference_image"]["present"]:
        next_action = "osbench reference build"
    elif not artifacts["inventory_manifest"]["present"]:
        next_action = "osbench reference inventory"
    elif not artifacts["rootfs_tar"]["present"] or not artifacts["oci_archive"]["present"]:
        next_action = "osbench reference export-oci"
    elif not calibration_ready:
        next_action = "osbench reference calibrate-unsynced --trials 20"
    else:
        next_action = "osbench reference lock-realize"

    return {
        "schema_version": "osbench.reference_preflight.v1",
        "reference_id": lock["reference_id"],
        "profile": profile_config.name,
        "source_lock_valid": source_lock["valid"],
        "source_lock_differences": source_lock["differences"],
        "tools": tools,
        "stages": stages,
        "artifacts": artifacts,
        "source_iso_valid": source_iso_valid,
        "calibration": {
            "ready": calibration_ready,
            "reason": calibration_reason,
            "binding_verified": calibration_binding_verified,
        },
        "realized_lock": {
            "ready": realized_lock_ready,
            "reason": realized_lock_reason,
            "binding_verified": realized_lock_binding_verified,
        },
        "materialization_ready": next_action is None,
        "next_action": next_action,
    }


def calibrate_unsynced_outcomes(
    *,
    trials: int = 20,
    profile: str | None = None,
    output: Path | None = None,
    seed: int = 73013,
) -> dict[str, Any]:
    if trials < 2:
        raise ValueError("unsynced calibration requires at least two trials")
    root = repo_root()
    profile_name = profile or os.environ.get("OSBENCH_PROFILE", "macos_tcg")
    if not profile_name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"invalid QEMU profile name: {profile_name!r}")
    image = root / "artifacts" / "reference" / "debian-13.6-amd64.qcow2"
    payload = root / "artifacts" / "payload" / "osbench-payload.iso"
    if not image.is_file():
        raise FileNotFoundError(image)
    if not payload.is_file():
        raise FileNotFoundError(payload)
    report = validate_contracts()
    contract = next(
        (
            value
            for value in report.contracts
            if value["id"] == "persistence.crash.unsynced_bounds"
        ),
        None,
    )
    if contract is None:
        raise KeyError("persistence.crash.unsynced_bounds")

    target = QemuTarget(image, profile=profile_name, payload_iso=payload)
    counts: Counter[str] = Counter()
    trial_records: list[dict[str, Any]] = []
    started = time.monotonic_ns()
    try:
        for index in range(trials):
            case = next(
                iter(generate_cases(
                    contracts=[contract],
                    profile="reference-calibration",
                    seed=seed + index,
                    cases_per_contract=1,
                ))
            )
            case["case_id"] = f"{case['case_id']}:calibration-{index:03d}"
            observation = target.execute(case)
            if observation.get("status") != "ok":
                raise RuntimeError(
                    f"unsynced calibration trial {index} failed: "
                    f"{observation.get('stderr', '')}"
                )
            verify = observation.get("observations", {}).get("verify", {})
            outcome = verify.get("outcome_class")
            if not isinstance(outcome, str):
                raise RuntimeError(
                    f"unsynced calibration trial {index} returned no outcome class"
                )
            required_invariants = {
                "durable_sentinel_intact": True,
                "no_cross_file_corruption": True,
                "plausible_unsynced_outcome": True,
                "block_granularity_valid": True,
            }
            violated = {
                key: verify.get(key)
                for key, expected in required_invariants.items()
                if verify.get(key) is not expected
            }
            if violated:
                raise RuntimeError(
                    f"unsynced calibration trial {index} violated invariants: {violated}"
                )
            counts[outcome] += 1
            trial_records.append(
                {
                    "trial": index,
                    "case_id": case["case_id"],
                    "seed": case["seed"],
                    "outcome": outcome,
                }
            )
    finally:
        target.close()

    document = {
        "schema_version": "osbench.accepted_outcomes.v1",
        "benchmark_version": BENCHMARK_VERSION,
        "reference_id": REFERENCE_ID,
        "contract": contract["id"],
        "profile": profile_name,
        "trial_count": trials,
        "seed": seed,
        "reference_image_sha256": sha256_file(image),
        "payload_sha256": sha256_file(payload),
        "outcomes": sorted(counts),
        "counts": dict(sorted(counts.items())),
        "trials": trial_records,
        "elapsed_seconds": (time.monotonic_ns() - started) / 1_000_000_000,
    }
    output = output or (
        root / "reference" / "oracle" / f"unsynced_outcomes.{profile_name}.json"
    )
    write_json(output, document)
    return {**document, "output": str(output)}


def _realize_container_environment(fields: dict[str, Any]) -> None:
    manifest = Path(
        os.environ.get(
            "OSBENCH_CONTAINER_PACKAGE_MANIFEST",
            "/usr/local/share/osbench/container-packages.tsv",
        )
    )
    if manifest.exists():
        fields["container_package_manifest_sha256"] = sha256_file(manifest)
        fields["container_package_count"] = sum(
            1 for line in manifest.read_text(errors="replace").splitlines() if line.strip()
        )


def _realize_installer(fields: dict[str, Any], root: Path) -> None:
    path = root / "artifacts" / "reference" / "installer" / "manifest.json"
    if not path.exists():
        return
    manifest = read_json(path)
    custom = manifest.get("custom_iso", {})
    injected = manifest.get("injected", {})
    fields["installer_iso_sha256"] = custom.get("sha256")
    fields["installer_iso_size_bytes"] = custom.get("size_bytes")
    fields["installer_initrd_sha256"] = injected.get("initrd_sha256")
    fields["installer_grub_cfg_sha256"] = injected.get("grub_cfg_sha256")
    fields["xorriso_version"] = manifest.get("xorriso_version")


def _realize_unsynced_calibration(
    fields: dict[str, Any],
    root: Path,
    *,
    profile_name: str,
) -> None:
    """Bind bounded crash semantics to the exact realized oracle artifacts.

    The unsynced-write Contract permits several durable outcomes, but only those
    empirically observed on the exact reference image, evaluator payload, and QEMU
    profile. A calibration file with stale metadata is intentionally ignored so a
    realized lock can never claim an accepted outcome set from another oracle.
    """

    path = root / "reference" / "oracle" / f"unsynced_outcomes.{profile_name}.json"
    if not path.is_file():
        return
    try:
        document = read_json(path)
    except (OSError, ValueError):
        return
    if not isinstance(document, dict):
        return

    outcomes = document.get("outcomes")
    valid = (
        document.get("schema_version") == "osbench.accepted_outcomes.v1"
        and document.get("benchmark_version") == BENCHMARK_VERSION
        and document.get("reference_id") == REFERENCE_ID
        and document.get("contract") == "persistence.crash.unsynced_bounds"
        and document.get("profile") == profile_name
        and document.get("reference_image_sha256") == fields.get("image_sha256")
        and document.get("payload_sha256") == fields.get("payload_sha256")
        and isinstance(outcomes, list)
        and bool(outcomes)
        and all(isinstance(outcome, str) and outcome for outcome in outcomes)
    )
    if not valid:
        return

    fields["unsynced_outcome_calibration_profile"] = profile_name
    fields["unsynced_outcome_calibration_path"] = path.relative_to(root).as_posix()
    fields["unsynced_outcome_calibration_sha256"] = sha256_file(path)
    fields["unsynced_outcome_calibration_trial_count"] = document.get("trial_count")
    fields["unsynced_outcome_calibration_outcomes"] = sorted(set(outcomes))


def realize_lock() -> dict[str, Any]:
    root = repo_root()
    source_path = root / "reference" / "lock.json"
    lock = read_json(source_path)
    realized = copy.deepcopy(lock)
    fields = realized["resolved_from_installed_system"]
    image = root / "artifacts" / "reference" / "debian-13.6-amd64.qcow2"
    inventory = root / "artifacts" / "reference" / "inventory" / "manifest.json"
    packages = root / "artifacts" / "reference" / "inventory" / "packages.tsv"

    _realize_container_environment(fields)
    _realize_installer(fields, root)

    if image.exists():
        fields["image_sha256"] = sha256_file(image)
    if inventory.exists():
        manifest = read_json(inventory)
        fields["package_manifest_sha256"] = manifest.get("package_manifest_sha256")
        fields["package_count"] = manifest.get("package_count")
    if packages.exists():
        package_versions: dict[str, str] = {}
        for line in packages.read_text(errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                package_versions[parts[0]] = parts[2]
        fields["kernel_package"] = next(
            (name for name in package_versions if name.startswith("linux-image-")),
            None,
        )
        kernel_package = fields["kernel_package"]
        fields["kernel_version"] = package_versions.get(kernel_package) if kernel_package else None
        fields["systemd_version"] = package_versions.get("systemd")
        fields["libc_version"] = package_versions.get("libc6")
        fields["coreutils_version"] = package_versions.get("coreutils")
        fields["shell_versions"] = {
            name: package_versions[name] for name in ("bash", "dash") if name in package_versions
        }
        fields["firmware_packages"] = sorted(
            name for name in package_versions if name.startswith("firmware-")
        )
    if shutil.which("qemu-system-x86_64"):
        fields["qemu_version"] = _first_version_line(["qemu-system-x86_64", "--version"])
    if not fields.get("xorriso_version") and shutil.which("xorriso"):
        fields["xorriso_version"] = _first_version_line(["xorriso", "-version"])
    ovmf = next(
        (
            Path(path)
            for path in ["/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_CODE.fd"]
            if Path(path).exists()
        ),
        None,
    )
    if ovmf:
        fields["ovmf_sha256"] = sha256_file(ovmf)
    rootfs = root / "artifacts" / "reference" / "debian-13.6-rootfs.tar"
    if rootfs.exists():
        fields["oci_rootfs_sha256"] = sha256_file(rootfs)
    oci_archive = root / "artifacts" / "reference" / "osbench-reference-13.6-v0.1.oci.tar"
    if oci_archive.exists():
        fields["oci_archive_sha256"] = sha256_file(oci_archive)
    workload_manifest = root / "artifacts" / "workloads" / "SHA256SUMS"
    if workload_manifest.exists():
        fields["workload_fixture_manifest_sha256"] = sha256_file(workload_manifest)
    probe_manifest = root / "artifacts" / "probes" / "SHA256SUMS"
    if probe_manifest.exists():
        fields["raw_probe_manifest_sha256"] = sha256_file(probe_manifest)
    payload = root / "artifacts" / "payload" / "osbench-payload.iso"
    if payload.exists():
        fields["payload_sha256"] = sha256_file(payload)

    profile_name = os.environ.get("OSBENCH_PROFILE", "macos_tcg")
    _realize_unsynced_calibration(fields, root, profile_name=profile_name)

    required = [
        fields["image_sha256"],
        fields["package_manifest_sha256"],
        fields["kernel_version"],
        fields["systemd_version"],
        fields["libc_version"],
        fields["payload_sha256"],
        fields["unsynced_outcome_calibration_sha256"],
    ]
    realized["status"] = "materialized" if all(required) else "partially_materialized"
    output = root / "artifacts" / "reference" / "lock.realized.json"
    write_json(output, realized)
    return {"status": realized["status"], "output": str(output), "resolved": fields}


def export_rootfs() -> dict[str, Any]:
    root = repo_root()
    script = root / "reference" / "build" / "export_rootfs.sh"
    completed = subprocess.run([str(script)], cwd=root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"rootfs export failed:\n{completed.stdout}\n{completed.stderr}")
    output = Path(completed.stdout.strip().splitlines()[-1])
    oci = build_oci_layout(
        output,
        output_dir=root / "artifacts" / "reference" / "oci-layout",
        archive_path=root
        / "artifacts"
        / "reference"
        / "osbench-reference-13.6-v0.1.oci.tar",
    )
    return {
        "rootfs": str(output),
        "sha256": sha256_file(output),
        "oci": oci,
        "docker_build": "docker build -f reference/oci/Dockerfile -t osbench-reference:13.6-v0.1 .",
        "docker_run": "docker run --rm -it osbench-reference:13.6-v0.1",
    }
