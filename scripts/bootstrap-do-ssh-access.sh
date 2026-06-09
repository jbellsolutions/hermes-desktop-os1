#!/usr/bin/env bash
# One-time: log in with root password, install this Mac's SSH key, probe Hermes.
# Usage: DO_ROOT_PASSWORD='...' bash bootstrap-do-ssh-access.sh single-brain
set -euo pipefail

HOST_ALIAS="${1:-single-brain}"
PUBKEY_FILE="${2:-$HOME/.ssh/id_ed25519.pub}"

if [[ ! -f "$PUBKEY_FILE" ]]; then
  echo "Missing public key: $PUBKEY_FILE" >&2
  exit 1
fi

if [[ -z "${DO_ROOT_PASSWORD:-}" ]]; then
  echo "Set DO_ROOT_PASSWORD to the emailed root password, then re-run." >&2
  exit 1
fi

if ! command -v sshpass >/dev/null 2>&1; then
  echo "Installing sshpass (one-time)..." >&2
  brew install hudochenkov/sshpass/sshpass
fi

PUBKEY="$(cat "$PUBKEY_FILE")"
REMOTE_CMD=$(cat <<EOF
set -e
mkdir -p ~/.ssh && chmod 700 ~/.ssh
grep -Fq '${PUBKEY}' ~/.ssh/authorized_keys 2>/dev/null || echo '${PUBKEY}' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo KEY_INSTALLED
EOF
)

HOST_IP="$(ssh -G "$HOST_ALIAS" 2>/dev/null | awk '/^hostname /{print $2}')"
HOST_IP="${HOST_IP:-$HOST_ALIAS}"

echo "Installing SSH key on ${HOST_ALIAS} (${HOST_IP})..."
if ! sshpass -p "$DO_ROOT_PASSWORD" ssh -F /dev/null \
  -o StrictHostKeyChecking=accept-new \
  -o PreferredAuthentications=password,keyboard-interactive \
  -o PubkeyAuthentication=no \
  "root@${HOST_IP}" "$REMOTE_CMD" 2>/dev/null; then
  echo
  echo "SSH password login is disabled on this droplet (normal for DO)."
  echo "Use the DO web console once, then re-run without DO_ROOT_PASSWORD:"
  echo "  https://cloud.digitalocean.com/droplets/$(doctl compute droplet list --format Name,ID --no-header | awk -v n="$HOST_ALIAS" '\$1==n{print \$2}')/console"
  echo
  echo "After console login, paste this single line:"
  echo "  $REMOTE_CMD"
  exit 2
fi

echo "Verifying key-based login..."
ssh -o BatchMode=yes "root@${HOST_ALIAS}" 'echo SSH_KEY_OK'

echo "Checking for Hermes..."
ssh "root@${HOST_ALIAS}" 'bash -s' <<'REMOTE'
set -euo pipefail
hermes_root="${HOME}/.hermes"
if [[ -d "$hermes_root" ]]; then
  echo "HERMES_ROOT=$hermes_root"
  ls -1 "$hermes_root/profiles" 2>/dev/null || true
  find "$hermes_root" -maxdepth 2 -name state.db 2>/dev/null | head -20
else
  echo "NO_HERMES_ROOT"
fi
if [[ -d /root/.ssh ]]; then
  echo "--- VPS SSH keys (for jumping to other droplets) ---"
  ls -la /root/.ssh 2>/dev/null || true
fi
REMOTE

echo "Done. Run: python3 $(dirname "$0")/sync-os1-connections.py"
