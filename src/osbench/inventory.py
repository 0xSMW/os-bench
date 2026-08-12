from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from .paths import repo_root
from .util import sha256_file, write_json


def _capture(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return completed.stdout if completed.returncode == 0 else completed.stderr


def collect_reference(
    output: Path | None = None,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Collect a normalized inventory from the current rootfs.

    The QEMU reference installer invokes this function inside the guest. Calling it
    on the host remains useful for validating the inventory format.
    """
    output = output or repo_root() / "artifacts/reference/inventory"
    output.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    sources = {
        "os_release": Path("/etc/os-release"),
        "resolv_conf": Path("/etc/resolv.conf"),
        "passwd": Path("/etc/passwd"),
        "group": Path("/etc/group"),
        "mounts": Path("/proc/mounts"),
        "proc_cpuinfo": Path("/proc/cpuinfo"),
        "proc_meminfo": Path("/proc/meminfo"),
        "proc_cmdline": Path("/proc/cmdline"),
    }
    for name, source in sources.items():
        if source.exists():
            destination = output / f"{name}.txt"
            destination.write_bytes(source.read_bytes())
            files[destination.name] = sha256_file(destination)

    commands = {
        "uname.txt": ["uname", "-a"],
        "mount.txt": ["mount"],
        "ip-address.txt": ["ip", "-details", "address"],
        "ip-route.txt": ["ip", "route", "show", "table", "all"],
        "sysctl.txt": ["sysctl", "-a"],
        "systemd-units.txt": ["systemctl", "list-unit-files", "--no-pager"],
        "systemd-enabled.txt": ["systemctl", "list-unit-files", "--state=enabled", "--no-pager"],
        "environment.txt": ["env"],
        "ldconfig.txt": ["ldconfig", "-p"],
    }
    for filename, command in commands.items():
        try:
            payload = _capture(command)
        except FileNotFoundError:
            continue
        destination = output / filename
        destination.write_text(payload, encoding="utf-8")
        files[filename] = sha256_file(destination)

    packages = output / "packages.tsv"
    try:
        completed = subprocess.run(
            ["dpkg-query", "-W", "-f=${binary:Package}\t${Architecture}\t${Version}\n"],
            capture_output=True,
            text=True,
            check=True,
        )
        packages.write_text(completed.stdout, encoding="utf-8")
    except (FileNotFoundError, subprocess.CalledProcessError):
        packages.write_text("", encoding="utf-8")
    files[packages.name] = sha256_file(packages)

    executable_inventory = output / "executables.tsv"
    rows: list[str] = []
    for directory in (Path("/bin"), Path("/sbin"), Path("/usr/bin"), Path("/usr/sbin")):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            try:
                if path.is_file() and os.access(path, os.X_OK):
                    rows.append(f"{path}\t{path.stat().st_size}\t{sha256_file(path)}")
            except OSError:
                continue
    executable_inventory.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    files[executable_inventory.name] = sha256_file(executable_inventory)

    manifest = {
        "schema_version": "osbench.inventory.v1",
        "profile": profile,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "kernel": platform.release(),
        "hostname": platform.node(),
        "uid": os.getuid() if hasattr(os, "getuid") else None,
        "files": dict(sorted(files.items())),
        "package_count": sum(1 for line in packages.read_text().splitlines() if line),
        "package_manifest_sha256": sha256_file(packages),
        "executable_count": len(rows),
    }
    write_json(output / "manifest.json", manifest)
    return {**manifest, "output": str(output)}
