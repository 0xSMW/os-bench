#!/bin/sh
set -eu
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
printf 'osbench-osbench-osbench\n' > "$D/input"; gzip -c "$D/input" > "$D/input.gz"; gzip -dc "$D/input.gz" > "$D/output"; cmp "$D/input" "$D/output"
printf '{"workload":"compression","status":"ok"}\n'
