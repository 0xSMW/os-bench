#!/bin/sh
set -eu
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
cd "$D"; git init -q; git config user.name OSBench; git config user.email osbench@local
printf osbench > file; git add file; git commit -qm initial
[ "$(git rev-list --count HEAD)" = 1 ]
printf '{"workload":"git","status":"ok","commits":1}\n'
