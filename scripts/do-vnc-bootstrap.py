#!/usr/bin/env python3
"""Legacy entrypoint — delegates to do-vnc-wget-bootstrap.py (wget install host).

VNC-safe install pattern (DO noVNC mangling):
  rm -f k.sh k.sh.1
  wget HOST/k.sh
  sh k.sh

Never type URLs with a scheme (colon breaks). Always remove stale k.sh first.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install SSH keys via noVNC wget bootstrap (wrapper)"
    )
    parser.add_argument("--droplet-id", type=int, required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--droplet-name", required=True)
    parser.add_argument("--fetch-pass", action="store_true", default=True)
    parser.add_argument("--no-fetch-pass", action="store_true")
    parser.add_argument("--root-pass")
    parser.add_argument("--no-new-pass", action="store_true")
    args = parser.parse_args()

    script = Path(__file__).resolve().parent / "do-vnc-wget-bootstrap.py"
    cmd = [
        sys.executable,
        str(script),
        "--droplet-id",
        str(args.droplet_id),
        "--ip",
        args.ip,
        "--droplet-name",
        args.droplet_name,
    ]
    if args.no_fetch_pass and args.root_pass:
        cmd.extend(["--root-pass", args.root_pass])
    elif not args.no_fetch_pass:
        cmd.append("--fetch-pass")
    if args.no_new_pass:
        cmd.append("--no-new-pass")

    proc = subprocess.run(
        ["uv", "run", "--with", "browser_cookie3", "--with", "playwright", *cmd],
        cwd=script.parent.parent,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
