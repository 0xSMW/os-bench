# Empirical oracle calibration

Unsynced writes have a bounded set of valid crash outcomes rather than one exact
post-crash byte sequence. `osbench reference calibrate-unsynced` repeatedly runs
the Contract on the exact QCOW2 image, payload, and QEMU profile. The resulting
accepted-outcome file is bound to both artifact hashes and validated against
`accepted-outcomes.schema.json`. No calibration is checked into the source tree
before the oracle is materialized.
