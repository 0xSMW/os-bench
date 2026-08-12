BENCHMARK_VERSION = "0.1.0"
REFERENCE_ID = "debian-13.6-amd64-osbench-v0.1"
LEVELS = [
    "boot", "machine", "linux_primitives", "kernel_subsystems",
    "linux_process_environment", "posix_userspace", "linux_system",
    "distro", "package_ecosystem", "real_workloads", "full_reconstruction",
]
CASE_FAMILIES = [
    "primitive", "boundary", "state_transition", "composition", "concurrency",
    "isolation", "failure", "persistence", "exhaustion", "workload", "performance",
]
