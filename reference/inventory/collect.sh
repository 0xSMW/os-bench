#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${1:-$ROOT/artifacts/reference/debian-13.6-amd64.qcow2}"
OUT="${2:-$ROOT/artifacts/reference/inventory}"
[ -f "$IMAGE" ] || { echo "missing reference image: $IMAGE" >&2; exit 1; }
rm -rf "$OUT" "$OUT.tmp"
mkdir -p "$OUT.tmp"
virt-copy-out -a "$IMAGE" /var/lib/osbench/inventory "$OUT.tmp"
if [ -d "$OUT.tmp/inventory" ]; then mv "$OUT.tmp/inventory" "$OUT"; else mv "$OUT.tmp" "$OUT"; fi
rm -rf "$OUT.tmp" 2>/dev/null || true
[ -f "$OUT/manifest.json" ] || { echo 'guest inventory manifest is missing; boot the image first' >&2; exit 1; }
printf '%s\n' "$OUT"
