#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/artifacts/packages}"
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT" ;; esac
EPOCH="${SOURCE_DATE_EPOCH:-1700000000}"
export SOURCE_DATE_EPOCH="$EPOCH"
BUILD_ROOT="$(mktemp -d /tmp/osbench-packages.XXXXXX)"
trap 'rm -rf "$BUILD_ROOT"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT/repository"
for V in 0.1.0 0.2.0; do
  D="$BUILD_ROOT/build-$V"
  mkdir -p "$D/DEBIAN" "$D/usr/bin" "$D/usr/share/osbench-hello" "$D/etc" "$D/usr/lib/systemd/system"
  chmod 0755 "$D" "$D/DEBIAN" "$D/usr" "$D/usr/bin" "$D/usr/share" "$D/usr/share/osbench-hello" "$D/etc" "$D/usr/lib" "$D/usr/lib/systemd" "$D/usr/lib/systemd/system"
  cat > "$D/DEBIAN/control" <<CONTROL
Package: osbench-hello
Version: $V
Section: utils
Priority: optional
Architecture: all
Maintainer: OSBench <osbench@local>
Depends: coreutils
Description: deterministic OSBench package lifecycle fixture
CONTROL
  printf '/etc/osbench-hello.conf\n' > "$D/DEBIAN/conffiles"
  for S in preinst postinst prerm postrm; do
    cat > "$D/DEBIAN/$S" <<SCRIPT
#!/bin/sh
set -e
mkdir -p /var/lib/osbench-package
printf '%s %s %s\\n' '$S' '$V' "\${1:-}" >> /var/lib/osbench-package/maintainer.log
exit 0
SCRIPT
    chmod 0755 "$D/DEBIAN/$S"
  done
  sed "s/unknown/$V/" "$ROOT/workloads/packages/osbench-hello.sh" > "$D/usr/bin/osbench-hello"
  chmod 0755 "$D/usr/bin/osbench-hello"
  printf 'version=%s\n' "$V" > "$D/etc/osbench-hello.conf"
  printf '%s\n' "$V" > "$D/usr/share/osbench-hello/version"
  cp "$ROOT/workloads/packages/osbench-hello.service" "$D/usr/lib/systemd/system/"
  find "$D" -print0 | xargs -0 touch -h -d "@$EPOCH"
  dpkg-deb --root-owner-group --build "$D" "$BUILD_ROOT/osbench-hello_${V}_all.deb" >/dev/null
  cp "$BUILD_ROOT/osbench-hello_${V}_all.deb" "$OUT/repository/"
done
(
  cd "$OUT/repository"
  if command -v dpkg-scanpackages >/dev/null 2>&1; then
    dpkg-scanpackages . /dev/null > Packages 2>/dev/null
  else
    python3 "$ROOT/workloads/packages/make_packages_index.py" "$OUT"
  fi
  gzip -n -9 -c Packages > Packages.gz
  cat > Release <<'RELEASE'
Origin: OSBench
Label: OSBench
Suite: stable
Codename: osbench
Architectures: all
Components: main
Description: deterministic offline corpus
RELEASE
)
python3 - "$OUT" "$ROOT/workloads/packages/lock.json" <<'PY'
import hashlib,json,pathlib,sys
out,lock=map(pathlib.Path,sys.argv[1:]); rows=[]
for p in sorted((out/'repository').glob('*.deb')):
 rows.append({'package':'osbench-hello','version':p.name.split('_')[1],'architecture':'all','filename':p.name,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
d={'schema_version':'osbench.offline_packages.v1','source_date_epoch':1700000000,'packages':rows}
lock.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n'); (out/'manifest.json').write_text(json.dumps(d,sort_keys=True,indent=2)+'\n'); print(json.dumps({'count':len(rows),'output':str(out)},sort_keys=True))
PY
(
  cd "$OUT"
  find . -type f ! -name SHA256SUMS -printf '%P\n' | LC_ALL=C sort | xargs -r sha256sum > SHA256SUMS
)
