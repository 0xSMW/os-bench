#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SOURCE=${1:-$($ROOT/reference/build/acquire_iso.sh)}
OUT=${2:-"$ROOT/artifacts/reference/installer/debian-13.6-osbench.iso"}
WORK=${OSBENCH_ISO_WORK:-"$ROOT/artifacts/reference/installer/work"}
rm -rf "$WORK"; mkdir -p "$WORK/tree" "$(dirname "$OUT")"
xorriso -osirrox on -indev "$SOURCE" -extract / "$WORK/tree" >/dev/null 2>&1
chmod -R u+w "$WORK/tree"
mkdir -p "$WORK/tree/osbench/guest" "$WORK/tree/osbench/src"
cp "$ROOT/reference/build/preseed.cfg" "$WORK/tree/preseed.cfg"
cp "$ROOT/reference/guest/osbench_agent.py" "$WORK/tree/osbench/guest/"
cp "$ROOT/reference/guest/osbench-inventory.sh" "$WORK/tree/osbench/guest/"
cp "$ROOT/reference/guest/osbench-agent.service" "$WORK/tree/osbench/guest/"
cp -a "$ROOT/src/osbench/." "$WORK/tree/osbench/src/osbench/"
for INITRD in "$WORK/tree/install.amd/initrd.gz" "$WORK/tree/install.amd/gtk/initrd.gz"; do
  [[ -f "$INITRD" ]] || continue
  D="$WORK/initrd-$(basename "$(dirname "$INITRD")")"; rm -rf "$D"; mkdir -p "$D"
  (cd "$D"; gzip -dc "$INITRD" | cpio -id --quiet; cp "$ROOT/reference/build/preseed.cfg" preseed.cfg; find . -print0 | cpio --null -o -H newc --quiet | gzip -9 > "$INITRD.new")
  mv "$D/$INITRD.new" "$INITRD"
done
python3 - "$WORK/tree" <<'PYI'
from pathlib import Path
import sys
root=Path(sys.argv[1])
needle='auto=true priority=critical preseed/file=/cdrom/preseed.cfg console=ttyS0,115200n8'
for rel in ('boot/grub/grub.cfg','isolinux/txt.cfg','isolinux/gtk.cfg'):
 p=root/rel
 if not p.exists(): continue
 s=p.read_text(errors='replace')
 s=s.replace('--- quiet',f'{needle} --- quiet').replace('---',f'{needle} ---',1)
 p.write_text(s)
PYI
rm -f "$OUT"
xorriso -indev "$SOURCE" -outdev "$OUT" -map "$WORK/tree" / -boot_image any replay -commit >/dev/null 2>&1
python3 - "$SOURCE" "$OUT" "$ROOT/artifacts/reference/installer/manifest.json" <<'PYI'
import hashlib,json,pathlib,subprocess,sys
src,out,manifest=map(pathlib.Path,sys.argv[1:])
def rec(p): return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
d={'schema_version':'osbench.installer_manifest.v1','source_iso':rec(src),'custom_iso':rec(out)}
pathlib.Path(manifest).write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
PYI
printf '%s\n' "$OUT"
