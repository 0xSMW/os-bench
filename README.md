# OSBench

OSBench is a behavioral benchmark for measuring whether an AI coding system can reconstruct a bootable Linux-compatible operating system. A candidate supplies source and a deterministic build command that produces an amd64 disk image. OSBench executes generated workloads against a pinned Debian reference and the candidate, normalizes only declared nondeterminism, then compares externally visible behavior.

The v0.1 repository contains 266 versioned Contracts, a validated capability DAG, 2,660 deterministic public cases, host-executable paths for 220 Contracts, 46 additional QEMU/guest-only mappings, ten freestanding amd64 raw-syscall probes, 18 workload manifests, deterministic evaluator-media and OCI-layout builders, hierarchical scoring, reference inventory and tracing tools, and a Docker/QEMU path designed for macOS Docker Desktop. Every Contract now has an execution mapping; the unsynced-write crash Contract remains fail-closed until its accepted outcome set is calibrated on the materialized reference.

## Start

Local development with Python 3.11 or newer:

```bash
python3 -m pip install -e '.[dev]'
osbench contracts validate
osbench graph build
osbench dataset build --profile public --seed 1 --check-determinism
pytest
osbench oracle selftest
osbench oracle full-selftest
osbench smoke
osbench eval --target reference
```

Docker Desktop on macOS:

```bash
docker compose build
docker compose run --rm osbench doctor
docker compose run --rm osbench reference preflight
docker compose run --rm osbench payload build
docker compose run --rm osbench reference-build
docker compose run --rm osbench reference-boot
docker compose run --rm osbench reference-inventory
docker compose run --rm osbench reference export-oci
docker compose run --rm osbench reference calibrate-unsynced --trials 20
docker compose run --rm osbench reference lock-realize
docker compose run --rm osbench contracts-validate
docker compose run --rm osbench dataset-build
docker compose run --rm osbench oracle-selftest
docker compose run --rm osbench full-selftest
docker compose run --rm osbench smoke
docker compose run --rm osbench eval --target reference
docker compose run --rm osbench shell
```

The primary Docker service uses the host container architecture and runs `qemu-system-x86_64` with TCG. Apple Silicon therefore avoids forcing an amd64 userspace container around an already emulated amd64 guest. The optional `osbench-kvm` profile is for Linux x86-64 hosts with `/dev/kvm` and official performance measurements.

## Reference system

The authoritative v0.1 source is the Debian 13.6.0 amd64 DVD-1 ISO. `reference/lock.json` pins its exact URL, byte size, and SHA-256 digest. `reference/build/build_image.sh` injects an unattended installer configuration, installs the serial evaluator agent, creates an 8 GiB QCOW2 image, and runs the installer under fixed Q35/OVMF virtual hardware.

The source lock deliberately leaves installed package, kernel, libc, systemd, QEMU, OVMF, image, and rootfs digests unresolved until they are measured from the built artifact. Run:

```bash
osbench reference lock-sources --check
osbench reference preflight
osbench payload build
osbench reference build
osbench reference inventory
osbench reference export-oci
osbench reference calibrate-unsynced --trials 20
osbench reference lock-realize
```

`osbench reference preflight` is read-only. It reports missing tools and artifacts, checks source-lock and artifact metadata, and returns the next command. Add `--verify-hashes` to cryptographically verify present QCOW2, payload, rootfs, OCI, and calibration artifacts before declaring the oracle ready.

The realized lock is written under `artifacts/reference/`. Its `materialized` status requires the image, installed package identity, payload, and a profile-specific unsynced-write calibration whose embedded image and payload hashes match the exact oracle. Large images and generated observations remain outside Git.

The bootable QEMU image is the kernel and full-system oracle. The derived rootfs export produces a deterministic OCI image layout and OCI archive for fast userspace and distro inspection; the conventional Dockerfile consumes the same rootfs tar:

```bash
osbench reference export-oci
# OCI layout: artifacts/reference/oci-layout/
# OCI archive: artifacts/reference/osbench-reference-13.6-v0.1.oci.tar
docker build -f reference/oci/Dockerfile -t osbench-reference:13.6-v0.1 .
docker run --rm -it osbench-reference:13.6-v0.1
```

The OCI representation shares the Docker VM kernel and therefore cannot grade kernel behavior.

## Contracts and generated cases

A Contract describes one observable behavior: its abstraction, operation, prerequisites, evidence, invariants, error behavior, state transitions, legal nondeterminism, cleanup requirements, composition surfaces, generator, and target transport. `contracts/schema/contract.schema.json` is authoritative.

The case grammar is:

```text
Case = abstraction × operation × state × composition × interference × fault × scale
```

`osbench dataset build` deterministically expands each Contract into concrete public cases. Hidden evaluation keeps the Contract visible while changing seeds, values, names, layouts, schedules, resource limits, failure points, and higher-order compositions.

Add a Contract by creating one YAML file below `contracts/<domain>/`, then run:

```bash
osbench contracts validate
osbench graph build
osbench dataset build --profile public --seed 1 --check-determinism
pytest
```

`tools/bootstrap_contracts.py` contains the curated v0.1 bootstrap catalog. It is retained for reproducibility; accepted YAML files remain the benchmark source of truth.

## Capability graph

Prerequisite edges create a DAG from firmware boot through complete workflows. Useful queries:

```bash
osbench graph prerequisites fs.file.rename.atomicity
osbench graph unlocked process.fork.basic
osbench graph workload sqlite
osbench graph blocked sync.futex.wait_wake
osbench graph frontier results/run.json
```

`frontier` returns unsatisfied nodes whose direct prerequisites pass. This is the next implementation surface for a progressive AI coding agent.

## Differential evaluation

The reference and candidate receive the same case. Raw observations are stored separately. Contract-specific normalization handles values such as PIDs, inodes, temporary paths, timestamps, ephemeral ports, directory order, and legal scheduling variation. The comparator then checks exact, set/range, or declared semantic equivalence. Crash outcomes whose exact state is intentionally unspecified use a pinned accepted-outcome calibration file produced by repeated execution on the immutable oracle.

Local self-evaluation uses host probes to validate the compiler, Contracts, generators, normalizers, comparators, result schema, and scoring without needing QEMU. `osbench oracle selftest` runs one representative case per Contract. `osbench oracle full-selftest` runs every public case in isolated process shards, recycles each local probe worker after a bounded number of requests, enforces a timeout per shard, preserves per-case progress journals, and merges the complete shard set into `results/full-local-selftest.json`. When the reference image exists, ordinary evaluation selects QEMU automatically. Set `OSBENCH_REFERENCE_MODE=local` only to force the non-authoritative host harness path.

Long evaluations can also be sharded manually:

```bash
osbench eval --target reference --shard-count 32 --shard-index 0 --output results/shard-00.json
# Run indices 0 through 31, then merge them:
osbench results merge results/shard-*.json --output results/merged.json
```

Every evaluator run writes `run.state.json`, an append-only `run.journal.jsonl`, incremental raw-observation JSONL files, and periodic partial results beneath `artifacts/oracle/<run-id>/`. These files identify the exact case and probe active before a timeout or crash.

Evaluate a candidate image:

```bash
osbench eval --target artifacts/candidate/disk.qcow2
```

Boot-only candidates are graded through serial output. Higher levels use the documented serial case protocol. A candidate may implement that control shim in any language; the bundled Python agent is the reference implementation. `osbench payload build` creates read-only evaluator media containing the agent, Python probes, raw syscall probes, a deterministic offline apt repository, package fixtures, and workload fixtures. Raw binaries reduce the dependency surface of the behavior under test, while the candidate-side control shim still launches them and returns their observations. QMP controls evaluator-owned lifecycle actions such as virtio block-device hotplug and abrupt power loss without trusting guest claims.

## Levels

| Level | Capability |
|---|---|
| `boot` | Firmware entry, kernel progress, root mount, PID 1, shutdown, reboot |
| `machine` | Privilege transitions, traps, exceptions, interrupts, page tables, devices, SMP |
| `linux_primitives` | ELF execution and foundational Linux syscall objects |
| `kernel_subsystems` | Processes, memory, files, IPC, scheduling, signals, networking, synchronization |
| `linux_process_environment` | Dynamic loading, TLS, threads, `/proc`, `/sys`, `/dev`, TTYs |
| `posix_userspace` | Shell and common portable utilities |
| `linux_system` | Linux-specific control, namespaces, capabilities, epoll, cgroups |
| `distro` | Debian identity, configuration, init, services, logging, persistence |
| `package_ecosystem` | Dpkg, offline package transactions, scripts, dependencies, services |
| `real_workloads` | Unmodified programs and application workflows |
| `full_reconstruction` | Long workflows crossing install, service, users, reboot, and crash recovery |

Levels are cumulative; every higher-level run retains earlier regressions.

## Scoring

`OSCorrect` applies a boot gate and weighted geometric aggregation across the complete Contract corpus; unsupported or unevaluated Contracts contribute zero. `Depth90` reports the deepest contiguous level prefix whose cumulative Contract-family correctness remains at least 90%, so a candidate cannot recover a missing foundational level by passing later easy cases. `ObservedCorrect` and `ObservedDepth90` describe only the exercised surface and are diagnostic harness metrics. `Native_p` reports correct macro workloads within a reference time/resource multiplier. The macOS TCG profile suppresses official `Native_p` values because host and guest emulation dominate timing.

Every result includes evaluated Contract coverage. A perfect host selftest proves the host-executable benchmark path; QEMU-only boot, hardware, service, package, hotplug, and persistence paths still require the materialized oracle.

## Repository map

```text
contracts/             accepted behavioral Contracts and schema
capability_graph/      generated DAG, DOT graph, workload closures
src/osbench/           CLI, compiler, oracle, targets, QEMU, scoring
probes/                 freestanding/raw-syscall probe runtime
workloads/              executable fixtures and workload manifests
reference/              pinned source, installer, agent, inventory, OCI export
dataset/                public JSONL cases and manifests
tools/                   discovery, tracing, coverage, minimization scaffolds
tests/                   validation and regression tests
docs/                    design, architecture, threat model, provenance
artifacts/               ignored images, traces, inventory, raw observations
results/                 ignored evaluation result files
```

## Current v0.1 boundary

All 266 Contracts have an execution mapping: 220 are registered for the current Linux host and 46 require the QEMU guest, VM lifecycle orchestration, QMP, Debian package state, or reference-only hardware. No Contract is waiting for a probe. One Contract, `persistence.crash.unsynced_bounds`, waits for empirical outcome calibration after the reference QCOW2 and payload ISO exist. `osbench doctor` reports that distinction explicitly. An environment without Docker, QEMU, OVMF, xorriso, libguestfs, or network access cannot materialize and boot the pinned 3.7 GiB Debian DVD-1 reference.
