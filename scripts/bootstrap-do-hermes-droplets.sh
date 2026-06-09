#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="${ROOT}/scripts/config/droplets.json"
EXAMPLE="${ROOT}/scripts/config/droplets.example.json"
PY="uv run --with browser_cookie3 --with playwright python3"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG — copy $EXAMPLE and edit your droplets." >&2
  exit 1
fi

bootstrap_one() {
  local id="$1" ip="$2" name="$3" extra="${4:-}"
  echo "========== $name ($ip) =========="
  doctl compute droplet-action password-reset "$id" --format ID --no-header >/dev/null
  sleep 30
  $PY "$ROOT/scripts/do-vnc-wget-bootstrap.py" \
    --droplet-id "$id" --ip "$ip" --droplet-name "$name" \
    --fetch-pass --screenshot "/tmp/vnc-${name}.png" $extra
}

python3 - "$CONFIG" <<'PY' | while IFS=$'\t' read -r id ip name flags; do
import json
import sys

data = json.load(open(sys.argv[1]))
for entry in data.get("droplets", []):
    flags = " ".join(entry.get("flags", []))
    print(f"{entry['id']}\t{entry['ip']}\t{entry['name']}\t{flags}")
PY
  [[ -n "${id:-}" ]] || continue
  bootstrap_one "$id" "$ip" "$name" "$flags" || true
done

echo "Done batch bootstrap"
