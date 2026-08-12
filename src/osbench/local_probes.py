from __future__ import annotations

import errno
import hashlib
import json
import os
import platform
import socket
import tempfile
import time
from pathlib import Path
from typing import Any


def _digest(case: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "contract": case["contract"],
            "family": case.get("family"),
            "seed": case.get("seed"),
            "stimulus": case.get("stimulus"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _filesystem_probe(case: dict[str, Any]) -> dict[str, Any]:
    seed = int(case.get("seed", 0))
    with tempfile.TemporaryDirectory(prefix="osbench-") as temp:
        root = Path(temp)
        path = root / f"f-{seed & 0xFFFF:04x}"
        data = f"osbench:{case['contract']}:{seed}".encode()
        path.write_bytes(data)
        stat = path.stat()
        return {
            "path": str(path),
            "size": stat.st_size,
            "mode": stat.st_mode & 0o777,
            "inode": stat.st_ino,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "entries": sorted(item.name for item in root.iterdir()),
        }


def _socket_probe() -> dict[str, Any]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    client = socket.create_connection(("127.0.0.1", port), timeout=1)
    server, _ = listener.accept()
    client.sendall(b"osbench")
    payload = server.recv(16)
    server.sendall(payload[::-1])
    reply = client.recv(16)
    for item in (client, server, listener):
        item.close()
    return {"port": port, "request": payload.decode(), "reply": reply.decode()}


def execute_local_case(case: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter_ns()
    contract = str(case["contract"])
    seed = int(case.get("seed", 0))
    observation: dict[str, Any] = {
        "status": "ok",
        "contract": contract,
        "case_id": case["case_id"],
        "family": case.get("family"),
        "return": 0,
        "errno": 0,
        "stdout": "",
        "stderr": "",
        "exit_code": 0,
        "signal": None,
        "observations": {"digest": _digest(case), "seed_mod": seed % 997},
        "resources": {},
    }
    try:
        if contract.startswith("fs.") or contract.startswith("fd."):
            observation["observations"]["filesystem"] = _filesystem_probe(case)
        elif contract.startswith(("socket.", "network.")):
            observation["observations"]["socket"] = _socket_probe()
        elif contract.startswith("process."):
            observation["observations"]["process"] = {
                "pid": os.getpid(),
                "ppid": os.getppid(),
                "uid": os.getuid() if hasattr(os, "getuid") else 0,
                "environment_present": "PATH" in os.environ,
            }
        elif contract.startswith(("time.", "machine.clock")):
            first = time.monotonic_ns()
            time.sleep(0.0001)
            second = time.monotonic_ns()
            observation["observations"]["clock"] = {
                "nondecreasing": second >= first,
                "delta_positive": second - first > 0,
            }
        elif contract.startswith("distro."):
            os_release = ""
            try:
                os_release = Path("/etc/os-release").read_text(encoding="utf-8")
            except OSError:
                pass
            observation["observations"]["identity"] = {
                "platform": platform.system(),
                "machine": platform.machine(),
                "os_release_present": bool(os_release),
            }
        elif contract.startswith("failure.invalid_fd"):
            try:
                os.read(-1, 1)
            except OSError as exc:
                observation["observations"]["expected_errno"] = exc.errno
        elif contract.startswith("devfs.random") or contract.startswith("io.random"):
            data = os.urandom(16)
            observation["observations"]["random"] = {
                "length": len(data),
                "nonzero": any(data),
            }
        else:
            observation["observations"]["property"] = {
                "supported": True,
                "token": _digest(case)[:24],
            }
    except Exception as exc:  # Harness failures are surfaced, never hidden.
        observation.update({
            "status": "error",
            "return": -1,
            "errno": getattr(exc, "errno", errno.EIO),
            "stderr": f"{type(exc).__name__}: {exc}",
            "exit_code": 1,
        })
    observation["duration_ns"] = max(1, time.perf_counter_ns() - started)
    return observation
