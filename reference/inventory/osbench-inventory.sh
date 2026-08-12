#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-/var/lib/osbench/inventory}"
mkdir -p "$OUT"
export LC_ALL=C TZ=UTC
copy_if() { [[ -e "$1" ]] && cp -L "$1" "$OUT/$2"; }
copy_if /etc/os-release os-release
copy_if /etc/passwd passwd
copy_if /etc/group group
copy_if /etc/resolv.conf resolv.conf
copy_if /proc/cmdline proc-cmdline
copy_if /proc/cpuinfo proc-cpuinfo
copy_if /proc/meminfo proc-meminfo
copy_if /proc/mounts proc-mounts
uname -a > "$OUT/uname.txt"
dpkg-query -W -f='${binary:Package}\t${Architecture}\t${Version}\n' | sort > "$OUT/packages.tsv"
find /bin /sbin /usr/bin /usr/sbin -xdev -type f -perm /111 -printf '%p\t%s\n' 2>/dev/null | sort > "$OUT/executables.tsv"
find /lib /usr/lib -xdev -type f \( -name '*.so' -o -name '*.so.*' \) -printf '%p\t%s\n' 2>/dev/null | sort > "$OUT/shared-libraries.tsv"
find /etc/systemd/system /usr/lib/systemd/system /lib/systemd/system -type f -o -type l 2>/dev/null | sort > "$OUT/systemd-units.txt"
systemctl list-unit-files --no-legend --no-pager 2>&1 | sort > "$OUT/systemd-unit-files.txt" || true
systemctl list-units --all --no-legend --no-pager 2>&1 | sort > "$OUT/systemd-runtime-units.txt" || true
mount | sort > "$OUT/mount.txt"
ip -details address > "$OUT/ip-address.txt" 2>&1 || true
ip route show table all > "$OUT/ip-route.txt" 2>&1 || true
sysctl -a > "$OUT/sysctl.txt" 2>&1 || true
lsmod > "$OUT/modules.txt" 2>&1 || true
find /dev -maxdepth 2 -printf '%y\t%m\t%u\t%g\t%p\n' 2>/dev/null | sort > "$OUT/devices.tsv"
find /proc -maxdepth 2 -type f -printf '%p\n' 2>/dev/null | sort > "$OUT/proc-files.txt"
find /sys -maxdepth 3 -printf '%y\t%p\n' 2>/dev/null | sort > "$OUT/sys-tree.txt"
env | sort > "$OUT/environment.txt"
ldconfig -p > "$OUT/ldconfig.txt" 2>&1 || true
(
  cd "$OUT"
  find . -type f ! -name SHA256SUMS ! -name manifest.json -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
python3 - "$OUT" <<'PY'
import hashlib,json,pathlib,platform,sys
out=pathlib.Path(sys.argv[1])
files={}
for path in sorted(out.iterdir()):
    if path.is_file() and path.name!='manifest.json':
        files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
packages=(out/'packages.tsv').read_text(errors='replace').splitlines()
executables=(out/'executables.tsv').read_text(errors='replace').splitlines()
document={
 'schema_version':'osbench.inventory.v1',
 'platform':platform.platform(),
 'machine':platform.machine(),
 'kernel':platform.release(),
 'hostname':platform.node(),
 'package_count':len(packages),
 'package_manifest_sha256':files.get('packages.tsv'),
 'executable_count':len(executables),
 'files':files,
}
(out/'manifest.json').write_text(json.dumps(document,sort_keys=True,indent=2)+'\n')
print(json.dumps(document,sort_keys=True))
PY
