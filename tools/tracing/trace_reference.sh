#!/usr/bin/env bash
set -euo pipefail
NAME=${1:?workload name required}
shift
exec osbench trace workload "$NAME" "$@"
