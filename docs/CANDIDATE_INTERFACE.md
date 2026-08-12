# Candidate interface

## Build contract

A submission is a source repository plus one deterministic build command. The command must produce one amd64 QCOW2 disk image at the declared output path without network access during official evaluation. Build inputs, compiler, linker, firmware-facing code, userspace, configuration, and generated files belong to the submission or allowed offline toolchain.

The evaluator records source revision, command, environment, wall time, output size, and image SHA-256.

## Virtual hardware

The candidate boots on Q35 with OVMF UEFI, two CPUs, 2 GiB RAM, virtio block, virtio network, a 16550A-compatible serial port, and virtio RNG. Exact values live in `config/qemu.yaml`.

## Boot transport

The candidate writes the following ASCII line to the first serial port after reaching the requested boot capability:

```text
OSBENCH_READY
```

A candidate may emit diagnostic output around the sentinel. The evaluator retains it. The sentinel satisfies only narrow boot progress; later cases require executable behavior.

## Evaluator payload

Run `osbench payload build` to create `artifacts/payload/osbench-payload.iso`. OSBench attaches this read-only ISO to candidate QEMU runs when it exists. It contains:

- The serial guest agent and generic Python probe modules.
- Ten freestanding amd64 raw-syscall probes.
- Two pinned offline Debian package fixtures.
- A deterministic offline apt repository containing both package versions.
- Compiled amd64 workload fixtures, including the real-time priority-inversion probe, and the workload manifest set.
- A bootstrap script for systems with a writable userspace and Python.

An early candidate may mount the ISO and execute raw binaries directly. The evaluator does not infer how to launch code inside an arbitrary candidate, so any Contract beyond the boot sentinel also requires a minimal candidate-side serial control shim that accepts the canonical case record, launches the requested asset, and returns an observation. The shim may be written in any language. A later candidate may run `osbench/bootstrap.sh`, which installs the Python reference agent and assets into the candidate filesystem. Candidate support for ISO9660, Python, systemd, or SSH is never assumed by earlier Contracts.

## Structured serial transport

Evaluation beyond the boot sentinel uses newline-delimited records on the first serial port. The bundled Python agent implements this protocol for Debian; it is not a required candidate architecture.

The evaluator sends:

```text
OSBENCH_CASE <base64-encoded canonical JSON case>
```

The guest returns:

```text
OSBENCH_RESULT <base64-encoded JSON observation>
```

The observation shape is:

```json
{
  "status": "ok",
  "return": 0,
  "errno": 0,
  "stdout": "",
  "stderr": "",
  "exit_code": 0,
  "signal": null,
  "observations": {},
  "resources": {},
  "duration_ns": 0
}
```

The benchmark supplies generic probes and workload assets. Candidate-specific expected values, case-ID bypasses, and evaluator-channel spoofing are prohibited.

## Lifecycle

Correctness cases normally run from a clean snapshot. Stateful sequences preserve one VM through their phases. Persistence cases use a writable overlay and orderly reboot. Crash cases terminate QEMU abruptly and restart from the resulting overlay. Every run has a deterministic seed and recorded QEMU command.

Some hardware cases are evaluator-orchestrated. OSBench uses QMP to attach and remove a uniquely identified virtio block device while the VM is running. The candidate observes ordinary guest hardware events and device state; it does not receive QMP access. Abrupt power-loss cases likewise terminate QEMU from the evaluator side.

Unsynced-write crash behavior is compared against an accepted outcome set calibrated from the exact pinned reference image and payload. Durable sentinels, block-granularity constraints, and absence of cross-file corruption remain mandatory in every accepted outcome.

## Exit classification

Unsupported transport is recorded separately. Malformed guest output, timeout, evaluator-channel closure, VM reset, or crash fails the case. Diagnostic output remains available in run artifacts.
