# Architecture

## Data flow

```text
Contract YAML
  → schema and semantic validation
  → capability DAG
  → seeded case compiler
  → reference and candidate targets
  → raw observations
  → Contract-specific normalization
  → semantic comparator
  → per-case and per-Contract results
  → OSCorrect, Depth90, Native_p
```

## Source modules

`contracts.py` loads one Contract per YAML file, validates JSON Schema, checks stable-ID uniqueness, resolves prerequisite and orthogonal references, and rejects graph cycles.

`graph.py` creates the DAG, exports YAML and DOT, computes prerequisites and descendants, maps workload closures, and finds the lowest unsatisfied frontier.

`dataset.py` derives each case seed from benchmark version, global seed, Contract ID, and index. Output order is Contract-ID order. Canonical JSON makes the manifest digest reproducible.

`probes.py`, `probes_extended.py`, and `probes_system.py` register host-executable paths for 220 Contracts. These validate benchmark mechanics and representative semantics without replacing the pinned VM oracle.

`probes/runtime/` and `probes/syscall/` provide ten freestanding amd64 binaries that invoke Linux syscalls without libc. They form the lowest-dependency executable layer after ELF loading.

`qemu.py` is the only module that constructs QEMU commands. Every run receives a unique directory, disposable OVMF variables, serial and QMP sockets, command record, stdout, stderr, serial logs, and QMP transcripts.

`targets.py` adapts local and QEMU systems to one `supports/execute` interface. A QEMU candidate exposes the boot sentinel and later the serial case protocol. Clean-snapshot declarations restart the VM; stateful cases retain a session. Dedicated orchestrators create writable overlays for reboot and power-cut cases and use QMP for evaluator-controlled virtio block hotplug.

`oracle.py` selects cases, executes both targets, preserves raw observations, normalizes, compares, aggregates Contracts, scores, writes progress checkpoints, and produces a versioned result document. `full_selftest.py` runs the full public corpus in bounded process shards and merges the shard results.

`reference_runtime.py` creates read-only snapshot sessions or disposable writable QCOW2 overlays, keeping the pinned base image immutable.

`reference.py`, `inventory.py`, `tracing.py`, and `oci.py` preflight, build, and inspect the reference, collect guest inventory, trace workloads, export the rootfs, create a deterministic OCI layout/archive, calibrate bounded crash outcomes, synchronize source hashes, and realize measured artifact fields. The realized lock reaches `materialized` only when its crash-calibration digest is bound to the exact image, payload, and QEMU profile.

`payload.py` builds read-only evaluator media containing the serial agent, Python probes, raw probes, a locked offline apt repository, package fixtures, and workload fixtures. Payload staging builds into an isolated temporary tree, verifies fixture hashes and required files, normalizes timestamps, and records a canonical tree digest. `QemuTarget` attaches this media automatically when present.

## Execution coverage

The v0.1 corpus has 266 Contracts. The current Linux host registers 220 and QEMU adds 46 guest-only or lifecycle mappings. Every Contract is mapped. A missing QEMU image, payload, transport, or unsynced-outcome calibration remains visible as unsupported or infrastructure failure; it never becomes a pass.

## Transport progression

The earliest transport is a serial byte sentinel. Raw-syscall probes require only ELF loading and write/exit from the behavior under test. The evaluator payload exposes those low-dependency binaries on read-only media, while a minimal candidate-side serial control shim remains responsible for launching them and returning observations. The shim can be native code or the bundled Python reference agent. Shell and SSH become ordinary workloads only after their dependencies pass.

Transport dependencies are part of each Contract. Unsupported transport is reported separately from semantic failure.

## Snapshot and persistence model

Ordinary correctness cases run from QEMU snapshot state. A case marked `clean_snapshot` forces a fresh VM. Multi-phase cases can preserve one VM. Writable reference infrastructure uses temporary backing overlays. Persistence and crash evaluators operate on dedicated writable overlays, then reboot, shut down, or power-cut those overlays and compare the resulting state. Unsynced writes are classified by outcome class while durable sentinels and cross-file integrity remain mandatory.

## Artifact separation

Committed:

- Schemas, Contracts, generators, probes, workloads, manifests, source locks, configs, scripts, tests, and documentation.

Ignored:

- ISO cache, QCOW2 images, mutable OVMF variables, payload ISO, rootfs tar, inventories, traces, serial logs, raw observations, and result runs.

## Failure handling

QEMU boot, guest-agent requests, builds, and extraction steps have bounded timeouts. QEMU termination escalates from terminate to kill. Build scripts verify source and generated artifacts. Invalid Contracts stop dataset construction. Unsupported target transports never become passing cases. Raw observations survive comparator failure.
