"""Shared bootstrap settings for DigitalOcean VNC scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
DROPLETS_CONFIG = SCRIPT_DIR / "config" / "droplets.json"
EXAMPLE_CONFIG = SCRIPT_DIR / "config" / "droplets.example.json"


def load_install_settings() -> tuple[str, str]:
    host = os.environ.get("OS1_INSTALL_HOST", "").strip()
    script = os.environ.get("OS1_INSTALL_SCRIPT", "").strip() or "k.sh"

    if DROPLETS_CONFIG.exists():
        data = json.loads(DROPLETS_CONFIG.read_text())
        host = host or str(data.get("install_host", "")).strip()
        script = os.environ.get("OS1_INSTALL_SCRIPT", "").strip() or str(
            data.get("install_script", script)
        ).strip()

    if not host or host in {"YOUR_HTTP_HOST_IP", "127.0.0.1"}:
        raise SystemExit(
            "Set install_host in scripts/config/droplets.json "
            f"(copy from {EXAMPLE_CONFIG.name}) or export OS1_INSTALL_HOST."
        )
    return host, script


def wget_lines(host: str, script: str) -> list[str]:
    return [
        f"rm -f {script} {script}.1",
        f"wget {host}/{script}",
        f"sh {script}",
    ]
