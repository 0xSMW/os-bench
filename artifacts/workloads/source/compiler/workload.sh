#!/bin/sh
set -eu
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
cc /var/lib/osbench/workloads/source/compiler/hello.c -o "$D/hello"
[ "$("$D/hello")" = osbench-compiler-ok ]
printf '{"workload":"compiler","status":"ok"}\n'
