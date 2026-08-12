#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK="$ROOT/reference/lock.json"
CACHE_ROOT="${OSBENCH_CACHE:-$HOME/.cache/osbench}"
DEST="$CACHE_ROOT/reference"
mkdir -p "$DEST"
readarray -t META < <(python3 - "$LOCK" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))['source']
for key in ('url','checksum_url','signature_url','filename','sha256','size_bytes'):
 print(s[key])
PY
)
URL=${META[0]}; SUMS_URL=${META[1]}; SIGN_URL=${META[2]}; NAME=${META[3]}; EXPECTED=${META[4]}; SIZE=${META[5]}
ISO="$DEST/$NAME"; SUMS="$DEST/SHA256SUMS"; SIGN="$DEST/SHA256SUMS.sign"
fetch() {
  local url=$1 output=$2
  if [[ ! -s "$output" ]]; then
    curl --fail --location --retry 5 --retry-delay 5 --output "$output.part" "$url"
    mv "$output.part" "$output"
  fi
}
fetch "$SUMS_URL" "$SUMS"
fetch "$SIGN_URL" "$SIGN"
KEYRING=""
for candidate in /usr/share/keyrings/debian-role-keys.gpg /usr/share/keyrings/debian-archive-keyring.gpg; do
  [[ -f "$candidate" ]] && KEYRING=$candidate && break
done
if [[ -n "$KEYRING" ]]; then
  gpgv --keyring "$KEYRING" "$SIGN" "$SUMS" >/dev/null
else
  printf 'warning: Debian signing keyring unavailable; relying on the source hash pinned in reference/lock.json\n' >&2
fi
SUM_HASH=$(awk -v name="$NAME" '$2==name || $2=="*"name {print $1}' "$SUMS")
[[ "$SUM_HASH" == "$EXPECTED" ]] || { echo "checksum file does not bind $NAME to pinned hash" >&2; exit 1; }
fetch "$URL" "$ISO"
ACTUAL_SIZE=$(stat -c %s "$ISO")
[[ "$ACTUAL_SIZE" == "$SIZE" ]] || { echo "size mismatch: expected $SIZE got $ACTUAL_SIZE" >&2; exit 1; }
printf '%s  %s\n' "$EXPECTED" "$ISO" | sha256sum --check --status
printf '%s\n' "$ISO"
