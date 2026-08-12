# Failure minimization

`minimize_jsonl.py` performs deletion-based reduction over a JSONL sequence. The
predicate command receives the candidate file in place of `{}` and returns nonzero
while the failure remains. It is intended for syscall sequences, event schedules, and
multi-step workload cases captured from the oracle.
