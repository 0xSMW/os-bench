#!/bin/sh
set -eu
VERSION=${OSBENCH_HELLO_VERSION:-unknown}
printf 'osbench-hello %s\n' "$VERSION"
