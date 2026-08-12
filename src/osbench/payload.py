from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .paths import repo_root
from .util import sha256_file, sha256_tree, write_json


def _tree_hash(path: Path) -> str:
    return sha256_tree(path, exclude=("manifest.json",))


def stage_payload(output: Path | None = None) -> dict[str, Any]:
    root = repo_root()
    output = output or root / "artifacts/payload/staging"
    if output.exists():
        shutil.rmtree(output)
    for name in ("agent", "probes", "workloads", "packages", "source"):
        (output / name).mkdir(parents=True, exist_ok=True)
    for source, destination in (
        (root / "reference/guest/osbench_agent.py", output / "agent/osbench_agent.py"),
        (root / "reference/guest/osbench-inventory.sh", output / "agent/osbench-inventory.sh"),
        (root / "reference/guest/osbench-agent.service", output / "agent/osbench-agent.service"),
    ):
        if source.exists():
            shutil.copy2(source, destination)
    for source, name in (
        (root / "artifacts/probes", "probes"),
        (root / "artifacts/workloads", "workloads"),
        (root / "artifacts/packages", "packages"),
    ):
        if source.exists():
            shutil.copytree(source, output / name, dirs_exist_ok=True)
    shutil.copytree(root / "probes", output / "source/probes", dirs_exist_ok=True)
    shutil.copytree(root / "workloads", output / "source/workloads", dirs_exist_ok=True)
    manifest = {
        "schema_version": "osbench.payload.v1",
        "tree_sha256": _tree_hash(output),
        "files": sum(1 for path in output.rglob("*") if path.is_file()),
        "directories": sum(1 for path in output.rglob("*") if path.is_dir()),
    }
    write_json(output / "manifest.json", manifest)
    return {**manifest, "output": str(output)}


def validate_payload_tree(path: Path | None = None) -> dict[str, Any]:
    path = path or repo_root() / "artifacts/payload/staging"
    issues: list[str] = []
    required = [
        "agent/osbench_agent.py",
        "agent/osbench-inventory.sh",
        "source/probes/build.sh",
        "source/workloads/build.sh",
        "manifest.json",
    ]
    for relative in required:
        if not (path / relative).exists():
            issues.append(f"missing {relative}")
    if (path / "manifest.json").exists():
        from .util import read_json
        document = read_json(path / "manifest.json")
        if document.get("tree_sha256") != _tree_hash(path):
            issues.append("payload tree digest mismatch")
    return {
        "valid": not issues,
        "issues": issues,
        "path": str(path),
        "files": sum(1 for item in path.rglob("*") if item.is_file()) if path.exists() else 0,
    }


def build_payload(output: Path | None = None) -> dict[str, Any]:
    root = repo_root()
    stage = stage_payload()
    tree = Path(stage["output"])
    iso = output or root / "artifacts/payload/osbench-payload.iso"
    iso.parent.mkdir(parents=True, exist_ok=True)
    xorriso = shutil.which("xorriso")
    if not xorriso:
        return {
            **stage,
            "iso": str(iso),
            "built": False,
            "reason": "xorriso unavailable; staging tree is complete",
        }
    completed = subprocess.run(
        [xorriso, "-as", "mkisofs", "-R", "-J", "-V", "OSBENCH", "-o", str(iso), str(tree)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    return {
        **stage,
        "iso": str(iso),
        "iso_sha256": sha256_file(iso),
        "built": True,
    }
