#!/bin/sh
set -eu
if ! command -v sshd >/dev/null 2>&1; then printf '{"workload":"ssh","status":"unsupported"}\n'; exit 77; fi
sshd -t
printf '{"workload":"ssh","status":"ok","configuration_valid":true}\n'
