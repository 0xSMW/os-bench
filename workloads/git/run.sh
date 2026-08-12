#!/bin/sh
set -eu
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git init -q "$d"
git -C "$d" config user.email osbench@example.invalid
git -C "$d" config user.name OSBench
printf x > "$d/value"
git -C "$d" add value
git -C "$d" commit -qm fixture
git -C "$d" status --porcelain | grep -q '^$' || exit 1
