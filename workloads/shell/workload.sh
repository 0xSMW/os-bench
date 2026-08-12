#!/bin/sh
set -eu
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
printf 'gamma\nalpha\nbeta\n' > "$D/in"
RESULT=$(cat "$D/in" | sort | grep '^b')
[ "$RESULT" = beta ]
printf '{"workload":"shell","status":"ok","result":"%s"}\n' "$RESULT"
