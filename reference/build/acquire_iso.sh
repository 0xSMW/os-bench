#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CACHE=${OSBENCH_CACHE:-"$HOME/.cache/osbench"}
mkdir -p "$CACHE/reference"
readarray -t VALUES < <(python3 - "$ROOT/reference/lock.json" <<'PYI'
import json,sys
x=json.load(open(sys.argv[1]))['source']
print(x['url']); print(x['filename']); print(x['sha256']); print(x['size_bytes'])
PYI
)
URL=${VALUES[0]}; FILE=${VALUES[1]}; SHA=${VALUES[2]}; SIZE=${VALUES[3]}
DEST="$CACHE/reference/$FILE"
if [[ ! -f "$DEST" ]]; then
  curl --fail --location --retry 5 --continue-at - --output "$DEST" "$URL"
fi
ACTUAL_SIZE=$(stat -c %s "$DEST" 2>/dev/null || stat -f %z "$DEST")
[[ "$ACTUAL_SIZE" == "$SIZE" ]] || { echo "source ISO size mismatch: $ACTUAL_SIZE != $SIZE" >&2; exit 1; }
printf '%s  %s\n' "$SHA" "$DEST" | sha256sum --check --status || { echo "source ISO digest mismatch" >&2; exit 1; }
printf '%s\n' "$DEST"
