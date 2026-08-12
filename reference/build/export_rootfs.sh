#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${1:-$ROOT/artifacts/reference/debian-13.6-amd64.qcow2}"
OUT="${2:-$ROOT/artifacts/reference/debian-13.6-rootfs.tar}"
WORK="$ROOT/artifacts/reference/rootfs-work"
[[ -f "$IMAGE" ]] || { echo "missing reference image: $IMAGE" >&2; exit 1; }
command -v guestfish >/dev/null || { echo 'guestfish is required' >&2; exit 1; }
rm -rf "$WORK"; mkdir -p "$WORK/root"
guestfish --ro -a "$IMAGE" -i tar-out / "$WORK/raw.tar" >/dev/null
# Repack in a stable order so the OCI layer identity is reproducible for one rootfs state.
tar -xf "$WORK/raw.tar" -C "$WORK/root"
mkdir -p "$(dirname "$OUT")"
tar --sort=name --format=posix --numeric-owner --owner=0 --group=0 \
  --mtime='@1700000000' --pax-option=delete=atime,delete=ctime \
  -C "$WORK/root" -cf "$OUT" .
rm -rf "$WORK"
printf '%s\n' "$OUT"
