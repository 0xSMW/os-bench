# Development

Install with `python3 -m pip install -e '.[dev]'`. `scripts/validate.sh` performs the complete source-only validation path. `scripts/build-fixtures.sh` compiles all deterministic probe, workload, and package fixtures. QEMU reference materialization requires the Docker image or equivalent Debian packages listed in `Dockerfile`.
