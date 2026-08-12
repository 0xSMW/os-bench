# Sources and provenance

OSBench derives coverage and edge cases from authoritative interfaces, then converts them into independent behavioral Contracts. Upstream tests are evidence and discovery material; their pass counts are not the OSBench score.

## KernelBench

Source: `https://github.com/ScalingIntelligence/KernelBench`

Used for the progression from primitive tasks through compositions and complete architectures, randomized correctness evaluation, separate performance comparison, reproducible task artifacts, and thresholded correctness-plus-performance metrics. OSBench replaces `fast_p` with the directionally analogous `Native_p`, where lower candidate/reference resource ratios are better.

License: MIT according to the upstream repository.

## POSIX.1-2024

Source: `https://pubs.opengroup.org/onlinepubs/9799919799/`

Used as the portable skeleton for process, file, directory, descriptor, signal, thread, synchronization, time, socket, shell, and utility semantics. Linux- or Debian-specific behavior is never attributed to POSIX.

Copyright remains with IEEE and The Open Group. OSBench stores references and original behavioral tests, not copied standard text.

## Linux kernel ABI documentation

Sources:

- `https://docs.kernel.org/admin-guide/abi.html`
- `https://docs.kernel.org/dev-tools/kselftest.html`

Used to inventory userspace ABI files and identify small userspace tests that exercise individual kernel paths. Kselftest mappings remain provenance metadata.

Linux kernel documentation and source licensing applies upstream.

## Linux man-pages

Source: `https://man7.org/linux/man-pages/`

Used for Linux syscall details, errno conditions, state transitions, flags, and interactions beyond POSIX.

## Linux Test Project

Sources:

- `https://github.com/linux-test-project/ltp`
- `https://github.com/linux-test-project/kirk`

Used to discover reliability, robustness, syscall, filesystem, memory, scheduler, and namespace cases, and to study remote QEMU execution. Imported code must retain its upstream license; v0.1 contains mappings rather than copied LTP tests.

## syzkaller

Sources:

- `https://github.com/google/syzkaller`
- `https://github.com/google/syzkaller/blob/master/docs/syscall_descriptions.md`

Used for the idea of declarative interface descriptions that generate, mutate, execute, serialize, and minimize syscall sequences. OSBench Contracts add external invariants, equivalence, state, cleanup, composition, distro, workload, and persistence dimensions.

License: Apache-2.0 upstream.

## Debian and autopkgtest

Sources:

- `https://www.debian.org/News/2026/20260711.en.html`
- `https://cloudfront.debian.net/cdimage/release/13.6.0/amd64/iso-dvd/`
- `https://www.debian.org/doc/debian-policy/`
- `https://manpages.debian.org/testing/autopkgtest/autopkgtest.1.en.html`

The exact Debian installer image and checksum define the source reference. Debian Policy informs distro and package Contracts. Autopkgtest informs installed-package workload structure and testbed isolation.

Individual Debian packages retain their own licenses. The benchmark records package manifests and does not relicense them.

## Modern Operating Systems, fifth edition

Andrew S. Tanenbaum and Herbert Bos. Used as a conceptual taxonomy: abstractions and operations, resource management, isolation, hardware management, orthogonality, mechanism versus policy, concurrency, failure cleanup, and cumulative subsystem construction.

No book text is redistributed in this repository.

## Provenance fields

Every accepted Contract contains one or more source records. Source inspection may identify a behavior, but the Contract remains implementation-independent. Distro-specific expected values are accepted only after execution against the pinned reference. AI-proposed Contracts retain evidence, uncertainty, and review state before acceptance.
