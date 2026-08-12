# Harness compatibility surface

The executable harness lives in `src/osbench/`. This directory provides a stable repository-level map for tooling that expects the design layout from the OSBench specification.

| Design component | Implementation |
|---|---|
| CLI | `src/osbench/cli.py` |
| QEMU controller | `src/osbench/qemu.py` |
| transports and targets | `src/osbench/targets.py` |
| differential oracle | `src/osbench/oracle.py` |
| normalization | `src/osbench/normalization.py` |
| comparison | `src/osbench/comparators.py` |
| scoring | `src/osbench/scoring.py` |
| results | `src/osbench/results.py` |
