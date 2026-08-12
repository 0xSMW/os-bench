#!/bin/sh
set -eu
OUT=/var/lib/osbench/inventory
mkdir -p "$OUT"
cp /etc/os-release "$OUT/os-release" 2>/dev/null || true
cp /etc/passwd "$OUT/passwd"
cp /etc/group "$OUT/group"
cp /etc/resolv.conf "$OUT/resolv.conf" 2>/dev/null || true
uname -a > "$OUT/uname.txt"
cat /proc/cmdline > "$OUT/proc-cmdline.txt"
cat /proc/mounts > "$OUT/mounts.txt"
dpkg-query -W -f='${binary:Package}\t${Architecture}\t${Version}\n' | LC_ALL=C sort > "$OUT/packages.tsv"
systemctl list-unit-files --no-pager > "$OUT/systemd-units.txt" 2>&1 || true
ip -details address > "$OUT/ip-address.txt" 2>&1 || true
ip route show table all > "$OUT/ip-route.txt" 2>&1 || true
find /bin /sbin /usr/bin /usr/sbin -xdev -type f -perm /111 -printf '%p\t%s\n' 2>/dev/null | LC_ALL=C sort > "$OUT/executables.tsv"
python3 - "$OUT" <<'PY'
import hashlib,json,os,pathlib,platform,sys
out=pathlib.Path(sys.argv[1]); files={}
for p in sorted(x for x in out.iterdir() if x.is_file() and x.name!='manifest.json'):
 files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
pkg=out/'packages.tsv'
doc={'schema_version':'osbench.inventory.v1','platform':platform.platform(),'machine':platform.machine(),'kernel':platform.release(),'hostname':platform.node(),'uid':os.getuid(),'files':files,'package_count':sum(1 for x in pkg.read_text().splitlines() if x),'package_manifest_sha256':hashlib.sha256(pkg.read_bytes()).hexdigest(),'executable_count':sum(1 for x in (out/'executables.tsv').read_text().splitlines() if x)}
(out/'manifest.json').write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n')
PY
