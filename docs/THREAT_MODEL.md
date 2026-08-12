# Threat model

## Candidate capabilities

The candidate controls all software in its disk image, can inspect virtual hardware and workload inputs, can emit arbitrary serial output, can crash or hang, and may attempt to infer benchmark identity. It has no authorized access to host files, hidden seeds, reference observations, evaluator code outside mounted probe assets, or external networking.

## Gaming strategies and defenses

Hardcoded public case outputs are defeated by hidden inputs, names, layouts, counts, schedules, and compositions.

Case-ID detection is reduced by keeping IDs in the host control record and sending payload-oriented execution requests where possible.

Filename and payload special cases are exposed by independent random values and semantically equivalent pathways.

Static lookup tables cannot cover high-entropy stateful sequences, concurrency, exhaustion, persistence, and macro workloads.

Skipped work is detected through externally inspected files, descriptors, process relationships, sockets, packets, services, package databases, and reboot state.

Fake service state is checked by making requests, observing processes and logs, stopping, restarting, and rebooting.

Fake filesystem metadata is checked through permission enforcement, links, mappings, persistence, package ownership, and independent raw-disk or guest inspection.

Output spoofing is limited because serial claims are one observable among many. Host-side QEMU lifecycle and disk artifacts remain authoritative.

Oracle overfitting is constrained by bounded queries, private hidden cases, query logging, and novel compositions.

Evaluator exploitation is addressed through strict schemas, bounded lengths and timeouts, isolated run directories, no candidate-controlled host shell interpolation, restricted QEMU networking, immutable reference images, and raw-log preservation.

## Failure policy

Malformed observations, missing fields, timeout, VM reset, unexpected QEMU exit, resource-limit violation, or evaluator-channel corruption fail closed. Infrastructure failures are distinguished from candidate failures only when the same worker cannot pass the reference selfcheck.

## Secrets

No live credentials enter the candidate. Fixture keys and passwords are benchmark data with no authority outside the isolated VM. Logs redact host environment values outside the declared observation set.
