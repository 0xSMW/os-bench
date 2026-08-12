#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/artifacts/probes}"
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT" ;; esac
if command -v x86_64-linux-gnu-gcc >/dev/null 2>&1; then CC=x86_64-linux-gnu-gcc
elif [ "$(uname -m)" = x86_64 ] && command -v gcc >/dev/null 2>&1; then CC=gcc
else echo "an x86_64 Linux C compiler is required" >&2; exit 2; fi
make -C "$ROOT/probes" clean all OUT="$OUT" CC="$CC"
(
  cd "$OUT"
  find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%P\n' | LC_ALL=C sort | xargs -r sha256sum > SHA256SUMS
)
printf '%s\n' "$OUT"
