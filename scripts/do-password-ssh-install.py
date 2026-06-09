#!/usr/bin/env python3
"""Install OS1 SSH key via password auth when VNC bootstrap fails."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

PUB = Path.home() / ".ssh/id_ed25519.pub"


def load_fetch_password():
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("wget", root / "do-vnc-wget-bootstrap.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.fetch_reset_password


def install(host: str, password: str, new_password: str | None) -> None:
    import paramiko

    pubkey = PUB.read_text().strip()
    remote_script = f"""#!/bin/sh
KEY='{pubkey}'
install_for() {{
  user="$1"
  home=$(getent passwd "$user" | cut -d: -f6)
  [ -n "$home" ] || return 0
  mkdir -p "$home/.ssh"
  chmod 700 "$home/.ssh"
  printf '%s\\n' "$KEY" > "$home/.ssh/authorized_keys"
  chmod 600 "$home/.ssh/authorized_keys"
  chown -R "$user:$user" "$home/.ssh"
}}
install_for root
install_for claw
install_for ubuntu
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/98-os1-fix.conf <<'EOF'
PubkeyAuthentication yes
PasswordAuthentication yes
PermitRootLogin yes
AuthorizedKeysFile .ssh/authorized_keys
EOF
systemctl restart ssh || service ssh restart
echo FIX_DONE
"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        host,
        username="root",
        password=password,
        timeout=20,
        allow_agent=False,
        look_for_keys=False,
    )
    if new_password:
        client.exec_command(f"echo 'root:{new_password}' | chpasswd", timeout=30)
    stdin, stdout, stderr = client.exec_command(f"sh -s <<'EOS'\n{remote_script}\nEOS", timeout=120)
    out = stdout.read().decode()
    err = stderr.read().decode()
    code = stdout.channel.recv_exit_status()
    client.close()
    if code != 0:
        raise RuntimeError(f"remote install failed ({code}): {err or out}")
    if "FIX_DONE" not in out:
        raise RuntimeError(f"unexpected output: {out[:500]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--password")
    parser.add_argument("--droplet-name", help="Fetch DO reset password from Gmail")
    parser.add_argument("--new-pass", default="Os1Bootstrap2026Xy")
    args = parser.parse_args()

    password = args.password
    if not password:
        if not args.droplet_name:
            print("Need --password or --droplet-name", file=sys.stderr)
            return 1
        fetch = load_fetch_password()
        password = fetch(args.droplet_name)
        if not password:
            print("No Gmail password", file=sys.stderr)
            return 1
        print(f"Gmail password: {password}")

    try:
        install(args.ip, password, args.new_pass)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"SSH key installed on {args.ip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
