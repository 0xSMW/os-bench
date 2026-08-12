from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from .paths import repo_root
from .util import read_yaml, write_json


@dataclass(frozen=True)
class QemuProfile:
    name: str
    binary: str
    machine: str
    accelerator: str
    cpu: str
    memory_mb: int
    smp: int
    firmware_code_candidates: list[str]
    firmware_vars_candidates: list[str]
    disk_interface: str
    network_device: str
    rng_device: str
    boot_timeout_seconds: float
    case_timeout_seconds: float
    shutdown_timeout_seconds: float


@dataclass
class QemuRun:
    run_id: str
    command: list[str]
    process: subprocess.Popen[bytes]
    serial_path: Path
    qmp_path: Path
    vars_path: Path
    work_dir: Path
    stdout_path: Path
    stderr_path: Path
    stdout_handle: BinaryIO
    stderr_handle: BinaryIO


def load_profile(name: str | None = None) -> QemuProfile:
    document = read_yaml(repo_root() / "config" / "qemu.yaml")
    configured_name = name or os.environ.get(
        "OSBENCH_PROFILE", document.get("default_profile", "macos_tcg")
    )
    try:
        values = dict(document["profiles"][configured_name])
    except KeyError as exc:
        raise KeyError(f"Unknown QEMU profile: {configured_name}") from exc

    return QemuProfile(
        name=configured_name,
        binary=str(values.get("binary", "qemu-system-x86_64")),
        machine=str(values.get("machine", "q35")),
        accelerator=str(values.get("accelerator", "tcg")),
        cpu=str(values.get("cpu", "max")),
        memory_mb=int(values.get("memory_mb", 2048)),
        smp=int(values.get("smp", 2)),
        firmware_code_candidates=list(
            values.get(
                "firmware_code_candidates",
                values.get(
                    "firmware_code",
                    ["/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_CODE.fd"],
                ),
            )
        ),
        firmware_vars_candidates=list(
            values.get(
                "firmware_vars_candidates",
                values.get(
                    "firmware_vars",
                    ["/usr/share/OVMF/OVMF_VARS_4M.fd", "/usr/share/OVMF/OVMF_VARS.fd"],
                ),
            )
        ),
        disk_interface=str(values.get("disk_interface", "virtio")),
        network_device=str(values.get("network_device", "virtio-net-pci")),
        rng_device=str(values.get("rng_device", "virtio-rng-pci")),
        boot_timeout_seconds=float(values.get("boot_timeout_seconds", 180)),
        case_timeout_seconds=float(values.get("case_timeout_seconds", 30)),
        shutdown_timeout_seconds=float(values.get("shutdown_timeout_seconds", 20)),
    )


def _first_existing(candidates: list[str]) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    raise FileNotFoundError(f"None of the configured files exist: {candidates}")


class QemuController:
    """Single place for deterministic VM command construction and lifecycle control."""

    def __init__(self, profile: str | None = None) -> None:
        self.profile = load_profile(profile)

    def available(self) -> bool:
        return shutil.which(self.profile.binary) is not None

    def build_command(
        self,
        *,
        image: Path,
        serial_path: Path,
        qmp_path: Path,
        vars_path: Path,
        seed: int = 1,
        snapshot: bool = True,
        install_iso: Path | None = None,
        kernel: Path | None = None,
        initrd: Path | None = None,
        append: str | None = None,
        auxiliary_media: list[Path] | None = None,
    ) -> list[str]:
        profile = self.profile
        firmware_code = _first_existing(profile.firmware_code_candidates)
        command = [
            profile.binary,
            "-name",
            f"osbench-{seed}",
            "-machine",
            profile.machine,
            "-accel",
            profile.accelerator,
            "-cpu",
            profile.cpu,
            "-m",
            str(profile.memory_mb),
            "-smp",
            str(profile.smp),
            "-nodefaults",
            "-no-reboot",
            "-display",
            "none",
            "-monitor",
            "none",
            "-rtc",
            "base=utc,clock=vm",
            "-object",
            "rng-random,id=rng0,filename=/dev/urandom",
            "-device",
            f"{profile.rng_device},rng=rng0",
            "-drive",
            f"if=pflash,format=raw,readonly=on,file={firmware_code}",
            "-drive",
            f"if=pflash,format=raw,file={vars_path}",
            "-drive",
            f"file={image},if={profile.disk_interface},format=qcow2,cache=writeback,discard=unmap",
            "-netdev",
            "user,id=net0,restrict=on",
            "-device",
            f"{profile.network_device},netdev=net0",
            "-chardev",
            f"socket,id=serial0,path={serial_path},server=on,wait=off",
            "-serial",
            "chardev:serial0",
            "-qmp",
            f"unix:{qmp_path},server=on,wait=off",
        ]
        if snapshot:
            command.append("-snapshot")
        if install_iso is not None:
            command.extend(
                ["-drive", f"file={install_iso},media=cdrom,readonly=on,index=1"]
            )
        for index, medium in enumerate(auxiliary_media or [], start=2):
            command.extend(
                ["-drive", f"file={medium},media=cdrom,readonly=on,index={index}"]
            )
        if kernel is not None:
            command.extend(["-kernel", str(kernel)])
        if initrd is not None:
            command.extend(["-initrd", str(initrd)])
        if append is not None:
            command.extend(["-append", append])
        return command

    def start(
        self,
        image: Path,
        *,
        seed: int = 1,
        snapshot: bool = True,
        install_iso: Path | None = None,
        kernel: Path | None = None,
        initrd: Path | None = None,
        append: str | None = None,
        auxiliary_media: list[Path] | None = None,
        run_id: str | None = None,
    ) -> QemuRun:
        image = Path(image)
        if not image.is_file():
            raise FileNotFoundError(image)
        if not self.available():
            raise FileNotFoundError(f"QEMU binary is unavailable: {self.profile.binary}")

        run_id = run_id or f"{int(time.time())}-{uuid.uuid4().hex[:12]}"
        work_dir = repo_root() / "artifacts" / "runs" / run_id
        work_dir.mkdir(parents=True, exist_ok=True)
        serial_path = work_dir / "serial.socket"
        qmp_path = work_dir / "qmp.socket"
        for stale in (serial_path, qmp_path):
            stale.unlink(missing_ok=True)

        vars_source = _first_existing(self.profile.firmware_vars_candidates)
        vars_path = work_dir / vars_source.name
        shutil.copyfile(vars_source, vars_path)
        command = self.build_command(
            image=image,
            serial_path=serial_path,
            qmp_path=qmp_path,
            vars_path=vars_path,
            seed=seed,
            snapshot=snapshot,
            install_iso=install_iso,
            kernel=kernel,
            initrd=initrd,
            append=append,
            auxiliary_media=auxiliary_media,
        )
        stdout_path = work_dir / "qemu.stdout"
        stderr_path = work_dir / "qemu.stderr"
        stdout_handle = stdout_path.open("wb")
        stderr_handle = stderr_path.open("wb")
        write_json(
            work_dir / "run.json",
            {
                "schema_version": "osbench.qemu_run.v1",
                "run_id": run_id,
                "profile": self.profile.name,
                "seed": seed,
                "snapshot": snapshot,
                "image": str(image),
                "command": command,
            },
        )
        try:
            process = subprocess.Popen(
                command,
                stdout=stdout_handle,
                stderr=stderr_handle,
                cwd=repo_root(),
                start_new_session=True,
            )
        except Exception:
            stdout_handle.close()
            stderr_handle.close()
            raise
        return QemuRun(
            run_id=run_id,
            command=command,
            process=process,
            serial_path=serial_path,
            qmp_path=qmp_path,
            vars_path=vars_path,
            work_dir=work_dir,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            stdout_handle=stdout_handle,
            stderr_handle=stderr_handle,
        )

    @staticmethod
    def _connect_unix(run: QemuRun, path: Path, timeout: float) -> socket.socket:
        deadline = time.monotonic() + timeout
        last_error: OSError | None = None
        while time.monotonic() < deadline:
            if run.process.poll() is not None:
                run.stderr_handle.flush()
                stderr = run.stderr_path.read_text(errors="replace") if run.stderr_path.exists() else ""
                raise RuntimeError(f"QEMU exited before socket became available: {stderr}")
            if path.exists():
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    client.connect(str(path))
                    client.settimeout(0.25)
                    return client
                except OSError as exc:
                    last_error = exc
                    client.close()
            time.sleep(0.05)
        raise TimeoutError(f"Timed out connecting to {path}: {last_error}")

    @staticmethod
    def _connect_serial(run: QemuRun, timeout: float) -> socket.socket:
        return QemuController._connect_unix(run, run.serial_path, timeout)

    def wait_for_serial(
        self,
        run: QemuRun,
        *,
        sentinel: bytes = b"OSBENCH_READY",
        timeout: float | None = None,
        log_name: str = "serial.log",
    ) -> bytes:
        timeout = timeout or self.profile.boot_timeout_seconds
        client = self._connect_serial(run, timeout)
        deadline = time.monotonic() + timeout
        buffer = bytearray()
        try:
            while time.monotonic() < deadline:
                if run.process.poll() is not None:
                    break
                try:
                    chunk = client.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    time.sleep(0.05)
                    continue
                buffer.extend(chunk)
                if sentinel in buffer:
                    break
        finally:
            client.close()
            (run.work_dir / log_name).write_bytes(buffer)
        if sentinel not in buffer:
            self.stop(run)
            raise TimeoutError(
                f"Sentinel {sentinel!r} was not observed within {timeout}s; "
                f"serial log: {run.work_dir / log_name}"
            )
        return bytes(buffer)

    def agent_case(self, run: QemuRun, case: dict[str, Any], timeout: float) -> dict[str, Any]:
        client = self._connect_serial(run, timeout)
        request = base64.b64encode(json.dumps(case, sort_keys=True).encode()).decode()
        client.sendall(f"OSBENCH_CASE {request}\n".encode())
        deadline = time.monotonic() + timeout
        buffer = bytearray()
        try:
            while time.monotonic() < deadline:
                try:
                    chunk = client.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    continue
                buffer.extend(chunk)
                lines = bytes(buffer).splitlines()
                for line in lines:
                    if line.startswith(b"OSBENCH_RESULT "):
                        encoded = line.split(b" ", 1)[1]
                        return json.loads(base64.b64decode(encoded))
        finally:
            client.close()
        raise TimeoutError(f"Guest agent did not return case {case['case_id']}")

    def qmp(self, run: QemuRun, command: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        client = self._connect_unix(run, run.qmp_path, 10)
        file = client.makefile("rwb", buffering=0)
        try:
            greeting = json.loads(file.readline())
            file.write(json.dumps({"execute": "qmp_capabilities"}).encode() + b"\r\n")
            capability_reply = json.loads(file.readline())
            if "error" in capability_reply:
                raise RuntimeError(capability_reply["error"])
            request: dict[str, Any] = {"execute": command}
            if arguments:
                request["arguments"] = arguments
            file.write(json.dumps(request).encode() + b"\r\n")
            while True:
                reply = json.loads(file.readline())
                if "return" in reply or "error" in reply:
                    return {"greeting": greeting, "reply": reply}
        finally:
            file.close()
            client.close()

    def hotplug_block(self, run: QemuRun, image: Path, *, node_id: str = "osbenchhot0") -> dict[str, Any]:
        image = Path(image)
        self.qmp(
            run,
            "blockdev-add",
            {"node-name": node_id, "driver": "raw", "file": {"driver": "file", "filename": str(image)}},
        )
        return self.qmp(
            run,
            "device_add",
            {"driver": "virtio-blk-pci", "drive": node_id, "id": f"dev-{node_id}"},
        )

    def hotunplug_block(self, run: QemuRun, *, node_id: str = "osbenchhot0") -> dict[str, Any]:
        return self.qmp(run, "device_del", {"id": f"dev-{node_id}"})

    @staticmethod
    def _close_logs(run: QemuRun) -> None:
        for handle in (run.stdout_handle, run.stderr_handle):
            if not handle.closed:
                handle.flush()
                handle.close()

    def stop(self, run: QemuRun) -> None:
        if run.process.poll() is None:
            run.process.terminate()
            try:
                run.process.wait(timeout=self.profile.shutdown_timeout_seconds)
            except subprocess.TimeoutExpired:
                run.process.kill()
                run.process.wait(timeout=5)
        self._close_logs(run)

    @staticmethod
    def power_cut(run: QemuRun) -> None:
        if run.process.poll() is None:
            run.process.kill()
            run.process.wait(timeout=5)
        QemuController._close_logs(run)

    def boot_check(
        self,
        image: Path,
        *,
        seed: int = 1,
        sentinel: bytes = b"OSBENCH_READY",
        auxiliary_media: list[Path] | None = None,
    ) -> dict[str, Any]:
        run = self.start(image, seed=seed, snapshot=True, auxiliary_media=auxiliary_media)
        started = time.monotonic_ns()
        try:
            serial = self.wait_for_serial(run, sentinel=sentinel)
            return {
                "status": "ok",
                "return": 0,
                "errno": 0,
                "stdout": serial.decode(errors="replace"),
                "stderr": "",
                "exit_code": 0,
                "signal": None,
                "observations": {
                    "booted": True,
                    "sentinel": sentinel.decode(errors="replace"),
                    "run_id": run.run_id,
                    "command": run.command,
                },
                "resources": {},
                "duration_ns": time.monotonic_ns() - started,
            }
        finally:
            self.stop(run)
