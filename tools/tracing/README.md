# Workload tracing

`trace_reference.sh NAME` invokes the versioned workload manifest through the OSBench
tracer. When `strace` is present it records per-process syscall traces with timestamps,
file-descriptor targets, and bounded strings. The workload manifest supplies the
initial Contract mapping; `tools/coverage/build_workload_matrix.py` expands it through
the capability DAG.
