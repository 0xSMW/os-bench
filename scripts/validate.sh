#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
python3 -m compileall -q src tests tools reference/guest
python3 -m osbench contracts validate
python3 -m osbench graph build
python3 -m osbench dataset build --profile public --seed 1 --cases-per-contract 10 --check-determinism
python3 -m osbench dataset validate
python3 -m pytest
