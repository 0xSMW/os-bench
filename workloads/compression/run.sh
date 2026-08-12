#!/bin/sh
set -eu
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'osbench-compression\n%.0s' 1 2 3 4 > "$d/input"
gzip -n -c "$d/input" > "$d/input.gz"
gzip -dc "$d/input.gz" > "$d/output"
cmp "$d/input" "$d/output"
