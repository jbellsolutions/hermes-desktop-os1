#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="${ROOT}/scripts/config/droplets.json"
EXAMPLE="${ROOT}/scripts/config/droplets.example.json"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG — copy $EXAMPLE and edit your droplets." >&2
  exit 1
fi

HERMES_PROBE='python3 - <<"PY"
import json
import os

home = os.path.expanduser("~/.hermes")
out = {"host": os.uname().nodename, "profiles": []}

def scan(base: str, name: str) -> None:
    sessions_dir = os.path.join(base, "sessions")
    session_count = len(os.listdir(sessions_dir)) if os.path.isdir(sessions_dir) else 0
    has_db = os.path.exists(os.path.join(base, "state.db"))
    if session_count or has_db or (name != "default" and os.path.isdir(base)):
        out["profiles"].append(
            {"name": name, "sessions": session_count, "state_db": has_db}
        )

if os.path.isdir(home):
    scan(home, "default")
    profiles_dir = os.path.join(home, "profiles")
    if os.path.isdir(profiles_dir):
        for entry in sorted(os.listdir(profiles_dir)):
            path = os.path.join(profiles_dir, entry)
            if os.path.isdir(path):
                scan(path, entry)
print(json.dumps(out))
PY'

mapfile -t DROPLETS < <(python3 - "$CONFIG" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1]))
for entry in data.get("probe", []):
    print(f"{entry['name']}|{entry['ip']}")
PY
)

mapfile -t KEYS < <(python3 - "$CONFIG" <<'PY'
import json
import os
import sys

data = json.load(open(sys.argv[1]))
for key in data.get("ssh_keys", ["~/.ssh/id_ed25519"]):
    print(os.path.expanduser(key))
PY
)

mapfile -t USERS < <(python3 - "$CONFIG" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1]))
for user in data.get("ssh_users", ["root", "claw", "ubuntu"]):
    print(user)
PY
)

for droplet in "${DROPLETS[@]}"; do
  name="${droplet%%|*}"
  ip="${droplet##*|}"
  found=0
  for user in "${USERS[@]}"; do
    for key in "${KEYS[@]}"; do
      [[ -f "$key" ]] || continue
      if out=$(ssh -o BatchMode=yes -o ConnectTimeout=6 -o StrictHostKeyChecking=accept-new \
        -i "$key" "${user}@${ip}" "$HERMES_PROBE" 2>/dev/null); then
        if [[ "$out" == *'"profiles"'* ]]; then
          echo "OK|${name}|${ip}|${user}|${key}|${out}"
          found=1
          break 2
        fi
      fi
    done
  done
  if [[ "$found" -eq 0 ]]; then
    echo "NOSSH|${name}|${ip}"
  fi
done
