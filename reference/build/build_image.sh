#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${OSBENCH_REFERENCE_IMAGE:-$ROOT/artifacts/reference/debian-13.6-amd64.qcow2}"
INSTALLER="$($ROOT/reference/build/prepare_installer.sh)"
LOG="$ROOT/artifacts/reference/install.log"
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT" "$LOG"
qemu-img create -f qcow2 "$OUT" 8G >/dev/null
CODE=""; VARS=""
for p in /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd; do [[ -f "$p" ]] && CODE=$p && break; done
for p in /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd; do [[ -f "$p" ]] && VARS=$p && break; done
[[ -n "$CODE" && -n "$VARS" ]] || { echo 'OVMF firmware not found' >&2; exit 1; }
VARS_COPY="$ROOT/artifacts/reference/OVMF_VARS.install.fd"; cp "$VARS" "$VARS_COPY"
ACCEL="${OSBENCH_INSTALL_ACCEL:-tcg}"
CPU="${OSBENCH_INSTALL_CPU:-max}"
TIMEOUT="${OSBENCH_INSTALL_TIMEOUT:-14400}"
set +e
timeout --signal=TERM --kill-after=30 "$TIMEOUT" qemu-system-x86_64 \
  -name osbench-reference-install \
  -machine q35 -accel "$ACCEL" -cpu "$CPU" -m 2048 -smp 2 \
  -drive "if=pflash,format=raw,readonly=on,file=$CODE" \
  -drive "if=pflash,format=raw,file=$VARS_COPY" \
  -drive "file=$OUT,if=virtio,format=qcow2,cache=writeback" \
  -drive "file=$INSTALLER,media=cdrom,readonly=on" \
  -boot order=d -display none -serial "file:$LOG" -monitor none -no-reboot
STATUS=$?
set -e
if [[ $STATUS -ne 0 && $STATUS -ne 124 ]]; then
  echo "Debian installer failed with status $STATUS; see $LOG" >&2
  exit "$STATUS"
fi
qemu-img check "$OUT" >/dev/null
printf '%s\n' "$OUT"
