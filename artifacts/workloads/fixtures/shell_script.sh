#!/bin/sh
set -eu
value=$(printf 'z\na\n' | sort | head -n1)
[ "$value" = a ]
printf '%s\n' shell-script-ok
