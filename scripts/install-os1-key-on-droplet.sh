#!/usr/bin/env bash
set -euo pipefail

PUBKEY_FILE="${1:-$HOME/.ssh/id_ed25519.pub}"

if [[ ! -f "$PUBKEY_FILE" ]]; then
  echo "Missing public key: $PUBKEY_FILE" >&2
  exit 1
fi

echo "Paste this public key into the droplet root authorized_keys (DO web console):"
echo
cat "$PUBKEY_FILE"
echo
echo "Droplet consoles:"
doctl compute droplet list --format Name,ID --no-header | while read -r name id; do
  echo "  $name: https://cloud.digitalocean.com/droplets/${id}/console"
done
echo
echo "On the droplet, run:"
echo "  mkdir -p ~/.ssh && chmod 700 ~/.ssh"
echo "  echo '<paste pubkey>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo
echo "Then from this Mac:"
echo "  ssh <alias> echo ok"
echo "  python3 $(dirname "$0")/sync-os1-connections.py"
