from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .paths import repo_root
from .util import read_yaml, write_json


def trace_workload(
    name: str,
    output: Path | None = None,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    manifest = repo_root() / f"workloads/manifests/{name}.yaml"
    if not manifest.exists():
        raise FileNotFoundError(manifest)
    document = read_yaml(manifest)
    command = str(document["command"])
    output = output or repo_root() / f"artifacts/traces/{name}"
    output.mkdir(parents=True, exist_ok=True)
    trace_prefix = output / "strace"
    started = time.monotonic_ns()
    strace = shutil.which("strace")
    if strace:
        completed = subprocess.run(
            [strace, "-ff", "-ttt", "-yy", "-s", "256", "-o", str(trace_prefix), "/bin/sh", "-c", command],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        completed = subprocess.run(
            ["/bin/sh", "-c", command],
            capture_output=True,
            text=True,
            check=False,
        )
    result = {
        "schema_version": "osbench.trace.v1",
        "workload": name,
        "profile": profile,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_ns": time.monotonic_ns() - started,
        "strace_available": bool(strace),
        "trace_files": sorted(path.name for path in output.glob("strace*")),
        "contracts": document.get("contracts", []),
        "output": str(output),
    }
    write_json(output / "result.json", result)
    return result
