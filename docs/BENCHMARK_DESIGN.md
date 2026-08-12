# OSBench benchmark design

## Abstract

OSBench evaluates whether an AI coding system can reconstruct a bootable Linux-compatible operating system. The system receives behavioral specifications, an offline development environment, and bounded black-box access to a pinned Debian reference. It produces source that deterministically builds an amd64 disk image. Hidden generated workloads execute against both systems, and OSBench compares normalized external observations.

The benchmark lifts KernelBench's progression from primitives to compositions and complete architectures into operating-system construction. Progress begins at firmware and serial output, proceeds through the Linux ABI and kernel subsystems, then reaches userspace, Debian services and packages, real applications, persistence, and crash-spanning workflows.

## Motivation

Operating systems force long-horizon engineering across interfaces that interact unexpectedly. A plausible implementation of one syscall says little about descriptor inheritance, signal interruption, concurrent mappings, resource cleanup, reboot durability, or the ability to run a real program. OSBench therefore measures a cumulative repository and generated behavioral compositions rather than isolated code answers.

The benchmark asks three scientific questions:

- How far can an AI system build a coherent operating environment from observable behavior?
- Which capability frontiers consume the most iterations, oracle queries, and architectural repair?
- Does increased test-time compute produce broad semantic generalization or narrow benchmark patching?

## Task definition

A run fixes the benchmark version, reference lock, virtual hardware profile, build environment, resource budget, oracle-query budget, and hidden seed distribution. The candidate starts from an allowed repository state and produces a bootable disk image through one deterministic build command.

Candidate internals are unrestricted. A monolithic kernel, microkernel, library OS, userspace server architecture, translated runtime, or other design may pass when it exposes the required behavior. Implementation-source similarity is never a correctness criterion.

## Reference system

The v0.1 reference is Debian 13.6 amd64 built from the exact DVD-1 ISO pinned in `reference/lock.json`. A fixed Q35 machine exposes OVMF UEFI, virtio block and network devices, a serial console, a virtual entropy device, two virtual CPUs, and 2 GiB RAM.

Two artifacts derive from one installed package state:

- A QCOW2 image is authoritative for boot, kernel, persistence, init, package, and full-system behavior.
- A rootfs/OCI representation accelerates filesystem inventory and userspace-only checks where kernel behavior is irrelevant.

Every resolved version and digest is measured from the built image. Missing values remain null until materialization.

## Capability model

The core unit is a Contract. Each Contract names one external abstraction and operation, prerequisites, sources, observables, equivalence relation, invariants, errors, legal transitions, cleanup and resource invariants, nondeterminism, case dimensions, orthogonal composition surfaces, fault injections, generator, transport, and workload links.

Prerequisite edges form a DAG. A node becomes an implementation frontier when every direct prerequisite passes and the node does not. This gives an agent a reproducible next capability while preserving the full regression suite.

The taxonomy follows four responsibilities of a general-purpose operating system:

- Define abstractions such as process, address space, file, descriptor, mapping, signal, socket, device, service, and package.
- Provide primitive operations over them.
- Enforce isolation while permitting controlled sharing.
- Manage CPU, memory, time, storage, networking, and devices.

## Contracts

Contracts are behavioral and stable across candidate architecture. `fs.file.unlink_open`, for example, requires namespace removal while existing open descriptions retain access until their final reference closes. It does not prescribe dentries, inodes, VFS objects, reference counters, or a particular filesystem implementation.

Each Contract separates portable semantics, Linux-specific semantics, and Debian policy through provenance records. The Debian oracle resolves values and defaults the standards do not define.

Accepted Contract IDs are permanent within a benchmark major version. Semantic changes require a new version or successor ID.

## Case generation

The conceptual grammar is:

```text
Case = abstraction × operation × state × composition × interference × fault × scale
```

Public v0.1 expands every Contract into ten deterministic cases. Generator parameters include names, payloads, sizes, offsets, modes, counts, ports, and timeouts. A Contract's declared dimensions select primitive, boundary, state-transition, composition, concurrency, isolation, failure, persistence, exhaustion, workload, and performance families.

A high-value operation grows through a recurring sequence:

- Valid primitive behavior.
- Zero, one, page, boundary, maximum, and malformed inputs.
- Operation sequences over changing object state.
- Composition with independent abstractions.
- Concurrent interference and controlled schedules.
- Authorized and unauthorized identities.
- Failure before, during, and after tentative resource acquisition.
- Repetition to reveal leaks.
- Reboot or power-loss boundaries.
- Unmodified application workloads.
- Common-case and worst-case resource envelopes.

## Benchmark levels

`boot` reaches OS code, root state, PID 1, and lifecycle control.

`machine` exposes traps, exceptions, interrupts, translation, block and serial I/O, clocks, entropy, and SMP.

`linux_primitives` executes ELF programs and creates foundational process, descriptor, and file objects.

`kernel_subsystems` composes process lifecycle, memory, scheduling, signals, filesystems, IPC, synchronization, time, TTY, networking, and readiness.

`linux_process_environment` supports dynamic loading, TLS, threads, procfs, sysfs, devfs, and ordinary runtime expectations.

`posix_userspace` runs shell semantics and common portable utilities.

`linux_system` exposes Linux-specific controls such as epoll, clone sharing, namespaces, capabilities, cgroups, sysctl, and mount behavior.

`distro` matches Debian identity, hierarchy, accounts, configuration, systemd, logging, networking, and durable defaults.

`package_ecosystem` executes offline dpkg and apt transactions, scripts, dependencies, conffiles, libraries, and service installation.

`real_workloads` runs unmodified applications.

`full_reconstruction` spans cold boot, user creation, package installation, service operation, reboot, and crash recovery.

## Differential oracle

Each generated case executes from equivalent clean state. The evaluator records raw return values, errno, stdout, stderr, exit status, signals, files, metadata, permissions, links, process relationships, descriptors, mappings, sockets, packets, service state, mount state, package state, persistence, timing, and resources as declared by the Contract.

Evaluator-owned VM transitions use QMP. Hotplug Contracts attach and remove a uniquely identified virtio block device while the guest is running, then confirm appearance and disappearance through independent guest observations. Crash Contracts use writable QCOW2 overlays and abrupt QEMU termination so the candidate cannot substitute a graceful shutdown.

Raw observations are immutable debugging evidence. Normalization produces a second representation. Rules are Contract-specific: PID numbers can differ while parent relationships must agree; inode numbers can differ while link identity must agree; ephemeral ports can differ while connection behavior agrees; directory order may be treated as a set only where the API permits it.

A normalization rule may remove identity only when the Contract declares it irrelevant. Failed comparisons preserve the smallest divergent path.

## Hidden distributions

Hidden evaluation publishes Contracts and representative generators while withholding seeds and distribution parameters. Hidden cases vary:

- Names, path depth, byte values, Unicode and invalid bytes.
- Sizes around page, block, pipe, socket, descriptor, and package boundaries.
- Process and thread counts.
- Descriptor allocation history.
- UID/GID/group arrangements and modes.
- Memory layout and mapping overlap.
- Ports, packet segmentation, timing, and connection order.
- Concurrency schedules and fault points.
- Disk layouts, free-space pressure, reboot sequences, and package combinations.
- Higher-order compositions unseen in public cases.

A hidden case ID and seed are never visible to the candidate guest. Control and observation channels remain separate from workload inputs.

## Real workloads

Workload manifests identify commands and direct Contract dependencies. The graph computes transitive closures. Tracing records syscalls and runtime evidence from the pinned reference, then maps failures back to the lowest missing capability frontier.

The initial set contains 18 manifests covering static and dynamic ELF, shell, core utilities, pthreads, Python, SQLite, Git, compression, HTTP, DNS, TCP, SSH, compiler/linker, package database, package lifecycle, installed service, and reboot-service workflows. Workloads remain unmodified during candidate execution.

## Scoring

For complete-corpus level correctness values `C_l` and weights `w_l`:

```text
OSCorrect = boot_gate × exp(sum(w_l × log(max(C_l, ε))) / sum(w_l))
```

The geometric aggregation makes a missing subsystem expensive. The result always reports evaluated Contract coverage so a narrow perfect run cannot appear equivalent to full benchmark completion.

`Depth90` is the deepest contiguous level prefix whose cumulative Contract-family correctness remains at least 90%. Missing or unsupported Contracts count as zero, and traversal stops at the first level that falls below the threshold. A later collection of easy passes therefore cannot conceal a missing foundational subsystem. `ObservedDepth90` applies the same contiguous-prefix rule only to levels with actual observations and exists for harness diagnostics.

`Native_p` is the fraction of macro workloads that are correct and execute within `p` times the reference resource envelope. It is official only on the pinned Linux x86-64/KVM runner. Boot time, peak memory, image size, build time, source size, test cost, and oracle queries remain separate metrics.

## AI-agent evaluation

Trajectory events record first boot, first userspace execution, Contracts passed over time, level progression, regressions, repairs, builds, tests, oracle queries, tokens when supplied, wall time, source growth, image growth, and current frontier.

A progressive agent loop is:

```text
frontier → evidence → hypothesis → implementation → build → boot → differential case → minimize → repair → full regression
```

The benchmark does not require this policy; it records enough state to compare agent strategies.

## Threat model

Hardcoded public outputs are countered through hidden values and compositions. Fake service, file, or package state is checked through downstream behavior and persistence. Candidate-visible channels exclude expected observations. Reference state is restored from snapshots. Evaluator crashes and malformed output fail closed and preserve raw logs.

## Reproducibility

The source ISO, container base index digest, hardware profile, Contract corpus, dataset seed, generator version, case manifest hash, reference image digest, package manifest, QEMU, OVMF, and runner profile identify a result.

Public dataset regeneration with the same version and seed must produce the same SHA-256 digest. Reference-versus-reference execution must pass every deterministic executable case. Properties with deliberately nondeterministic but bounded outcomes use a profile-specific calibration artifact. The unsynced-write crash Contract repeatedly executes on the exact pinned QCOW2/payload pair, verifies durable sentinels and absence of cross-file corruption, and records only the outcome classes actually observed. Evaluation fails closed when that calibration is missing or tied to different artifact hashes.

## Limitations

The v0.1 corpus contains 266 Contracts. The local Linux harness registers 220 and the QEMU/guest path adds 46, so every Contract has an execution mapping. The QEMU-only surface includes firmware and boot, device hotplug, Debian service and package state, writable lifecycle overlays, and crash recovery. One crash Contract requires empirical accepted-outcome calibration after the exact reference image and payload are materialized. The 3.7 GiB ISO must be downloaded once, and this execution environment must provide Docker/QEMU/OVMF/libguestfs to build and validate the full oracle. Performance is intentionally absent from macOS TCG results. Exact concurrency replay, broader power-cut matrices, wider package diversity, and automatic trace-to-Contract inference remain expansion areas.

## Roadmap

The highest-value expansions are broader freestanding syscall coverage, deterministic scheduler perturbation and replay, a calibrated crash matrix across filesystems and QEMU cache modes, a broader signed offline package corpus, systematic kselftest/LTP mapping, syscall-description import, workload minimization, and controlled model-agent trajectory experiments.
