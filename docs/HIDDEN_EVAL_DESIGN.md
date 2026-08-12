# Hidden evaluation design

Public Contracts define the target semantics. Hidden evaluation measures implementation generality by withholding concrete distributions.

## Hidden material

- Global and per-suite seeds.
- Parameter ranges and biased boundary mixtures.
- Filenames, path graphs, payloads, modes, users, groups, environment strings, and ports.
- Descriptor allocation histories and process trees.
- Memory addresses, mapping topology, and pressure.
- Thread counts, barriers, wake order, and fault schedules.
- Disk fullness, inode pressure, package combinations, service dependencies, and reboot sequences.
- Macro workload compositions and perturbations.

## Distribution families

Each Contract receives ordinary, boundary, adversarial, and composition distributions. A hidden run samples all four. Public examples establish format and intent without covering the hidden support.

Pairwise orthogonal combinations are broad. Selected three- and four-way combinations follow traced application dependencies. For example, a hidden shell case may combine fork, descriptor inheritance, close-on-exec, pipeline backpressure, signal interruption, and process-group delivery.

## Leakage controls

Case IDs, hidden seeds, and reference observations remain outside the guest. Generated names do not include Contract IDs. The agent receives only the workload necessary to execute a case. Control messages and observation storage use evaluator-owned serial endpoints and host paths.

Leaderboard workers restore immutable images, use fresh run directories, and prevent candidate network access. Hidden datasets are generated on workers from signed benchmark code and private seed material.

## Anti-hardcoding checks

Canary cases alter irrelevant formatting while preserving semantics. Equivalent operations are expressed through different syscall and workload paths. Downstream macro cases verify state independently. Results are rejected when candidate output claims success while evaluator-observed files, sockets, processes, services, or persistent state disagree.
