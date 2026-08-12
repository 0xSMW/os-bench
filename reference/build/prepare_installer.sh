#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_ISO="${1:-$($ROOT/reference/build/download_iso.sh)}"
OUT="${2:-$ROOT/artifacts/reference/installer/debian-13.6-osbench-amd64.iso}"
WORK="$ROOT/artifacts/reference/installer/work"
rm -rf "$WORK"; mkdir -p "$WORK" "$(dirname "$OUT")"
ORIGINAL_GRUB="$WORK/grub.cfg"
xorriso -osirrox on -indev "$SOURCE_ISO" -extract /boot/grub/grub.cfg "$ORIGINAL_GRUB" >/dev/null 2>&1
python3 - "$ORIGINAL_GRUB" "$WORK/grub.osbench.cfg" <<'PY'
import pathlib,sys
source=pathlib.Path(sys.argv[1]).read_text(errors='replace')
append=' auto=true priority=critical preseed/file=/cdrom/preseed.cfg console=ttyS0,115200n8 serial ---'
lines=[]
for line in source.splitlines():
    stripped=line.lstrip()
    if stripped.startswith('linux ') or stripped.startswith('linuxefi '):
        line=line.replace(' --- quiet','').replace(' ---','') + append
    lines.append(line)
pathlib.Path(sys.argv[2]).write_text('\n'.join(lines)+'\n')
PY
STAGE="$WORK/osbench"; mkdir -p "$STAGE/packages"
cp "$ROOT/reference/guest/osbench_agent.py" "$STAGE/osbench_agent.py"
cp "$ROOT/reference/guest/osbench-agent.service" "$STAGE/osbench-agent.service"
cp "$ROOT/reference/guest/osbench-inventory.sh" "$STAGE/osbench-inventory.sh"
cp "$ROOT/reference/guest/install.sh" "$STAGE/install.sh"
if [[ -d "$ROOT/artifacts/packages/repository" ]]; then cp -a "$ROOT/artifacts/packages/repository/." "$STAGE/packages/"; fi
rm -f "$OUT"
xorriso -indev "$SOURCE_ISO" -outdev "$OUT" -boot_image any replay \
  -map "$ROOT/reference/build/preseed.cfg" /preseed.cfg \
  -map "$WORK/grub.osbench.cfg" /boot/grub/grub.cfg \
  -map "$STAGE" /osbench \
  -commit >/dev/null 2>&1
python3 - "$SOURCE_ISO" "$OUT" "$WORK/grub.osbench.cfg" "$ROOT/artifacts/reference/installer/manifest.json" <<'PY'
import hashlib,json,pathlib,subprocess,sys
source,custom,grub,manifest=map(pathlib.Path,sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
try: version=subprocess.run(['xorriso','-version'],capture_output=True,text=True).stdout.splitlines()[0]
except Exception: version=None
doc={'schema_version':'osbench.installer.v1','source_iso':{'path':str(source),'size_bytes':source.stat().st_size,'sha256':sha(source)},'custom_iso':{'path':str(custom),'size_bytes':custom.stat().st_size,'sha256':sha(custom)},'injected':{'preseed_sha256':sha(pathlib.Path('reference/build/preseed.cfg')),'grub_cfg_sha256':sha(grub)},'xorriso_version':version}
manifest.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n')
print(custom)
PY
