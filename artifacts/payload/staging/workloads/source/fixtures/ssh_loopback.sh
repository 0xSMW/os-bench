#!/usr/bin/env bash
set -euo pipefail
command -v ssh >/dev/null
ssh -V 2>&1 | head -n1
printf '%s\n' ssh-loopback-fixture-ready
