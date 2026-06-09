#!/usr/bin/env bash
set -euo pipefail

ALIAS="${1:-}"
PROFILE="${2:-}"

if [[ -z "$ALIAS" ]]; then
  echo "Usage: $0 <ssh-alias> [hermes-profile]" >&2
  exit 1
fi

ssh -o BatchMode=yes -o ConnectTimeout=8 "$ALIAS" python3 - "$PROFILE" <<'PY'
import json
import os
import sys

profile = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
base = os.path.expanduser("~/.hermes")
if profile:
    base = os.path.join(base, "profiles", profile)

sessions = os.path.join(base, "sessions")
state_db = os.path.join(base, "state.db")
ok = os.path.isdir(base)
payload = {
    "ok": ok,
    "base": base,
    "sessions_dir": os.path.isdir(sessions),
    "session_count": len(os.listdir(sessions)) if os.path.isdir(sessions) else 0,
    "state_db": os.path.exists(state_db),
}
print(json.dumps(payload, indent=2))
if not ok:
    raise SystemExit(1)
PY
