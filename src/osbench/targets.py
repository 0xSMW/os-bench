from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .probes import execute_case
from .qemu import QemuController, QemuRun


class Target(ABC):
    name: str

    @abstractmethod
    def supports(self, case: dict[str, Any]) -> bool: ...

    @abstractmethod
    def execute(self, case: dict[str, Any]) -> dict[str, Any]: ...

    def close(self) -> None:
        return None


class LocalTarget(Target):
    def __init__(self, name: str = "local-linux") -> None:
        self.name = name

    def supports(self, case: dict[str, Any]) -> bool:
        transport = case.get("transport") or case.get("setup", {}).get("transport")
        return transport in {"host", "raw_syscall", "shell", "none"}

    def execute(self, case: dict[str, Any]) -> dict[str, Any]:
        return execute_case(case)


class QemuTarget(Target):
    def __init__(
        self,
        image: Path,
        profile: str | None = None,
        payload_iso: Path | None = None,
    ) -> None:
        self.image = Path(image)
        self.payload_iso = Path(payload_iso) if payload_iso else None
        self.controller = QemuController(profile)
        self.name = f"qemu:{self.image}"
        self.run: QemuRun | None = None

    def supports(self, case: dict[str, Any]) -> bool:
        return self.controller.available() and self.image.is_file()

    def _ensure_run(self, case: dict[str, Any]) -> QemuRun:
        if self.run is None:
            media = [self.payload_iso] if self.payload_iso and self.payload_iso.exists() else []
            self.run = self.controller.start(
                self.image,
                seed=int(case.get("seed", 1)),
                snapshot=True,
                auxiliary_media=media,
            )
            self.controller.wait_for_serial(self.run)
        return self.run

    def execute(self, case: dict[str, Any]) -> dict[str, Any]:
        run = self._ensure_run(case)
        return self.controller.agent_case(
            run,
            case,
            timeout=float(case.get("timeout_seconds", 30)),
        )

    def close(self) -> None:
        if self.run is not None:
            self.controller.stop(self.run)
            self.run = None
