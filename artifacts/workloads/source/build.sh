#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-"$ROOT/artifacts/workloads"}
case "$OUT" in
  /*) ;;
  *) OUT="$PWD/$OUT" ;;
esac

rm -rf "$OUT"
mkdir -p "$OUT/bin" "$OUT/fixtures" "$OUT/source"

CC=${CC:-gcc}
CROSS=${CROSS_CC:-x86_64-linux-gnu-gcc}
command -v "$CROSS" >/dev/null 2>&1 || CROSS=$CC

"$CROSS" -Os -static -s "$ROOT/workloads/static_elf/main.c" -o "$OUT/bin/static-elf"
"$CROSS" -Os -s "$ROOT/workloads/dynamic_elf/main.c" -o "$OUT/bin/dynamic-elf"
"$CROSS" -Os -s -pthread "$ROOT/workloads/pthread/main.c" -o "$OUT/bin/pthread"

# Keep stable root-level paths for tests and payload consumers while retaining
# the organized bin/ directory used by manifests and guest tooling.
for name in static-elf dynamic-elf pthread; do
  cp "$OUT/bin/$name" "$OUT/$name"
  chmod 0755 "$OUT/$name" "$OUT/bin/$name"
done

# Preserve the complete workload source corpus in the generated artifact.
cp -a "$ROOT/workloads"/. "$OUT/source/"

# Copy directly executable fixtures to the canonical fixture paths expected by
# the local harness and guest payload. Do not bury them beneath workloads/.
for fixture in shell_script.sh python_basic.py tcp_loopback.py http_loopback.py ssh_loopback.sh; do
  cp "$ROOT/workloads/fixtures/$fixture" "$OUT/fixtures/$fixture"
done
chmod 0755 "$OUT/fixtures"/*

# Also retain every script/service under its source-relative path for debugging,
# traceability, and workloads that refer to their directory structure.
mkdir -p "$OUT/fixtures/tree"
(
  cd "$ROOT"
  find workloads -type f \( -name '*.py' -o -name '*.sh' -o -name '*.service' \) \
    -exec cp --parents {} "$OUT/fixtures/tree/" \;
)

python3 - "$OUT" <<'PYI'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
rows = []
for path in sorted(p for p in root.rglob('*') if p.is_file() and p.name != 'manifest.json'):
    rows.append({
        'path': path.relative_to(root).as_posix(),
        'size': path.stat().st_size,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    })
(root / 'manifest.json').write_text(
    json.dumps(
        {'schema_version': 'osbench.workloads.v1', 'count': len(rows), 'files': rows},
        sort_keys=True,
        indent=2,
    ) + '\n',
    encoding='utf-8',
)
print(json.dumps({'count': len(rows), 'output': str(root)}, sort_keys=True))
PYI
