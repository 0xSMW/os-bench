# Reference distribution

## Immutable source

`reference/lock.json` pins Debian GNU/Linux 13.6 (`trixie`) for `amd64` from `debian-13.6.0-amd64-DVD-1.iso`:

- Exact byte size: `3,992,977,408`.
- SHA-256: `e97736b7f49af22497c8df95e381ea5025faf3575af4b7ca6d5f40971265364e`.
- Installer mirror access disabled.
- Docker build environment pinned to the Debian 13.6 slim multi-platform image index digest.
- Q35/OVMF hardware, CPU, RAM, SMP, storage, networking, serial, entropy, and disk format fixed in the source lock and `config/qemu.yaml`.

DVD-1 is used because it contains the installer and a broad offline package set. The reference installation therefore does not depend on a moving Debian mirror after the ISO is acquired.

The lock has two phases. Source fields are committed. Kernel, libc, systemd, shell, package-manifest, QEMU, OVMF, QCOW2, rootfs, built-workload, payload, and crash-calibration digests remain null until measured from a successful materialization. `osbench reference lock-realize` writes `artifacts/reference/lock.realized.json`; it never replaces missing values with guesses. The status becomes `materialized` only after the profile-specific crash calibration names the same image and payload hashes recorded in that lock.

Run `osbench reference preflight` before starting the multi-hour build. It checks the source lock, Docker/QEMU toolchain, OVMF files, current artifacts, calibration metadata, and reports the next required command without mutating the repository. Add `--verify-hashes` to verify the present multi-gigabyte ISO, QCOW2, payload, OCI artifacts, and calibration against their recorded digests. Add `--strict` to exit nonzero until the realized oracle is complete.

## Image construction

`reference/build/download_iso.sh` downloads the ISO into the shared cache and verifies both byte size and SHA-256.

`reference/build/prepare_installer.sh` extracts the installer kernel and initrd, then injects:

- The unattended preseed.
- The JSON-over-serial reference agent and systemd unit.
- The generic Python probe library.
- The inventory collector.
- Deterministically built amd64 static-ELF, dynamic-ELF, pthread, and priority-inversion fixtures.
- The locked two-version offline Debian package corpus and deterministic apt repository metadata.

Probe, workload, and package builds use isolated temporary output trees before their verified artifacts are copied into the installer. This prevents stale or concurrent global build outputs from affecting the customized ISO.

`reference/build/build_image.sh` creates a fresh 8 GiB QCOW2 disk and runs Debian Installer under Q35/OVMF-compatible hardware using TCG, two CPUs, 2 GiB RAM, virtio block, virtio network, and serial console. The installed image is checked with `qemu-img check`, then cold-booted from OVMF in snapshot mode. The build succeeds only after the serial log contains `OSBENCH_AGENT_READY`.

Generated files:

```text
artifacts/reference/debian-13.6-amd64.qcow2
artifacts/reference/install.log
artifacts/reference/first-boot.log
```

## Boot and agent protocol

A successful boot emits:

```text
OSBENCH_READY
OSBENCH_AGENT_READY
```

The first marker grades narrow boot progress. The second indicates that structured serial cases can execute. The QEMU controller preserves the exact command, profile, seed, mutable OVMF variables, serial transcript, QMP transcript, stdout, and stderr in a unique `artifacts/runs/<run-id>/` directory.

Normal QEMU cases use the immutable base image with QEMU snapshot semantics. Writable infrastructure operations use disposable QCOW2 overlays so the base reference remains unchanged.

Evaluator-owned hardware transitions use QMP. The device-hotplug Contract creates a raw backing file in the run directory, adds a virtio block backend and PCI device, verifies the guest-visible serial and size, removes the device, verifies disappearance, then deletes the backend. The guest never controls or attests the host-side transition.

## Inventory

`osbench reference inventory` boots a writable overlay, invokes `/usr/local/lib/osbench-inventory.sh`, syncs the filesystem, stops the VM, then extracts `/var/lib/osbench/inventory` with libguestfs. The authoritative inventory covers:

- OS and kernel identity, command line, kernel config, modules, CPU, memory, and filesystems.
- Package versions, dpkg selections and state hashes, apt sources, executables, shared libraries, loaders, and loader cache.
- Filesystem paths, modes, owners, groups, sizes, `/etc` hashes, device nodes, mounts, and block devices.
- Users, groups, credential-file metadata, locale, timezone, environment, and limits.
- Systemd units, enabled units, active units, and default target.
- `/proc` and `/sys` path surfaces, sysctls, network addresses, routes, rules, sockets, DNS, and hostname.

The normalized inventory and its per-file hashes are written to `artifacts/reference/inventory/manifest.json`. If the image or VM tools are unavailable, OSBench writes a separate, explicitly non-authoritative host fallback under `artifacts/reference/host-fallback/`; it is never used to realize the reference lock.

## Workload tracing

`osbench trace workload <name>` prefers the pinned VM. It runs the workload under `strace -f`, returns syscall names and counts through the serial agent, and writes a summary under `artifacts/traces/<name>/`. Without the VM, tracing is marked `local-host-fallback`.

`tools/coverage/build_workload_matrix.py` combines declared workload Contracts, transitive DAG prerequisites, and any observed trace data into `capability_graph/workload_matrix.json` and `docs/CAPABILITY_COVERAGE.md`.

## Offline package corpus

`workloads/packages/lock.json` pins two deterministic `osbench-hello` package versions. They exercise installation, preinst and postinst execution, dependencies, conffile preservation during upgrade, removal, purge, dpkg failure rollback, unit installation, service startup, local HTTP behavior, and package-state cleanup without network access. The payload also carries a deterministic apt repository with `Packages`, `Packages.gz`, `Release`, pool artifacts, and a complete SHA-256 manifest.

`workloads/packages/build.sh` builds and verifies both `.deb` files against their locked sizes and hashes. The artifacts are injected into the reference image at `/var/lib/osbench/packages/`.

## OCI representation

`reference/build/export_rootfs.sh` exports the installed root filesystem with libguestfs. `osbench reference export-oci` then creates a deterministic OCI image layout whose uncompressed layer is that exact rootfs tar, plus a portable OCI archive. The scratch image in `reference/oci/Dockerfile` remains available for a conventional Docker build:

```bash
osbench reference export-oci
# artifacts/reference/oci-layout/
# artifacts/reference/osbench-reference-13.6-v0.1.oci.tar
docker build -f reference/oci/Dockerfile -t osbench-reference:13.6-v0.1 .
docker run --rm -it osbench-reference:13.6-v0.1
```

The OCI representation is useful for package and filesystem inspection. It shares the Docker VM kernel and is never authoritative for kernel behavior, boot, hardware, persistence, or isolation.

## Crash-outcome calibration

`persistence.crash.unsynced_bounds` intentionally permits more than one durable result after abrupt power loss. Once the reference QCOW2 and payload ISO exist, run:

```bash
osbench reference calibrate-unsynced --trials 20
```

Each trial writes a durable sentinel and old file, overwrites the candidate file without `fsync`, kills QEMU, reboots the same overlay, classifies the candidate as old, new, or a block-aligned mixture, and requires the sentinel and unrelated files to remain intact. The resulting `reference/oracle/unsynced_outcomes.<profile>.json` records artifact hashes, trial seeds, counts, and only the outcome classes observed on the exact oracle. Run calibration before `osbench reference lock-realize`; the realized lock records the calibration digest and refuses `materialized` status when its profile, image hash, payload hash, benchmark version, or reference identity differs. The comparator likewise fails closed when the file is absent or mismatched.

## Source-lock maintenance

`osbench reference lock-sources` recomputes canonical hashes over the declared package, payload, raw-probe, reference-builder, and workload source sets. `osbench reference lock-sources --check` is used in CI and fails when committed source hashes are stale. The tree digest includes relative path, executable bit, byte length, and file digest, so it is independent of checkout location.

## Evaluator payload

`osbench payload build` creates `artifacts/payload/osbench-payload.iso`. QEMU candidate sessions attach it as read-only auxiliary media. The payload is built from the same locked raw probes, package fixtures, offline apt repository, workload fixtures, and agent sources injected into the reference installation, which keeps candidate and reference stimuli aligned. Staging validates required files and package hashes, normalizes timestamps, and records a canonical tree digest before ISO creation.
