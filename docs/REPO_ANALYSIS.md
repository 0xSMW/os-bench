# Repository analysis

## Starting state

The supplied workspace contained no OSBench repository, source files, build configuration, CI, tests, Docker assets, schemas, or generated artifacts. Only the operating-systems reference PDF was present. A new Git repository was initialized rather than modifying an unrelated project.

## Chosen stack

Python 3.11+ owns benchmark orchestration because it provides portable filesystem, process, JSON, schema, graph, and subprocess tooling across macOS Docker and Linux. Typer provides one CLI. JSON Schema validates Contracts and concrete cases. PyYAML stores human-reviewable Contracts and graph data. NetworkX validates and queries the capability DAG.

C remains the probe language where libc would hide the behavior under test. `probes/runtime/raw_syscall.h` issues amd64 syscalls directly, and the first freestanding probe verifies write and exit. Higher-level workloads use their natural runtime: C, pthreads, shell, Python, SQLite, Git, HTTP, package tools, and services.

QEMU is isolated behind `QemuController`. Evaluators never construct raw QEMU commands. The same controller supports TCG on macOS and KVM on Linux through declarative profiles.

## Architecture retained

There was no prior implementation to retain. The benchmark structure follows the requested Contract → generated case → target execution → normalization → comparison → scoring path. Large generated images and observations are excluded from Git; source locks, scripts, schemas, public cases, and manifests are committed.

## Implemented surfaces

- 266 accepted Contract YAML files across 35 domains.
- Formal Contract and concrete-case schemas.
- Capability DAG validation, export, frontier, dependency, and workload queries.
- Deterministic JSONL dataset compiler producing 2,660 public cases.
- Host-executable paths for 220 Contracts and 46 additional QEMU/guest-only mappings, covering all 266 Contracts.
- QEMU/OVMF controller, QMP control channel, serial boot sentinel, and serial JSON case protocol.
- Pinned Debian 13.6 DVD-1 ISO source and unattended reference-image builder.
- Rootfs export plus deterministic OCI image-layout and archive construction.
- Reference inventory and workload tracing.
- Hierarchical scoring and structured results.
- Test suite and CI workflow.
- AI-assisted Contract proposal schema and prompt.

## Deliberate boundaries

The host fallback validates benchmark machinery and representative Linux behavior. It is identified as `reference-host-fallback` in results and does not establish that the pinned Debian VM boot path ran. Official results require a materialized reference image and Linux KVM performance profile.

The guest agent supports the boot sentinel, generic Python probe dispatch, ten freestanding raw-syscall binaries, deterministic package and offline-apt lifecycle fixtures, block-device inspection, priority-inversion execution, inventory and tracing operations, lifecycle verification, and real workload manifests. QEMU orchestration adds clean overlays, orderly reboot and shutdown, abrupt power loss, and QMP-controlled block-device hotplug. Every accepted Contract has an execution mapping. The remaining unmaterialized condition is empirical calibration of the permitted unsynced-write crash outcomes on the pinned QCOW2 image.
