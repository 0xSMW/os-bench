#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
probes/build.sh
workloads/build.sh
workloads/packages/build.sh
python3 -m osbench payload stage
