#!/usr/bin/env python3
"""Probe SSH hosts and regenerate OS1 connections.json for reachable Hermes instances."""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REF = datetime(2001, 1, 1, tzinfo=UTC)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR / "config" / "hosts.json"
EXAMPLE_CONFIG = SCRIPT_DIR / "config" / "hosts.example.json"
OS1_DIR = Path.home() / "Library/Application Support/OS1"
CONNECTIONS_PATH = OS1_DIR / "connections.json"

HERMES_PROBE = r"""
python3 - <<'PY'
import json
import os

home = os.path.expanduser("~/.hermes")
out = {"host": os.uname().nodename, "profiles": []}

def scan(base, name):
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
PY
"""


@dataclass(frozen=True)
class HostSpec:
    alias: str
    label: str
    profile: str | None = None


def load_hosts(config_path: Path) -> list[HostSpec]:
    if not config_path.exists():
        raise SystemExit(
            f"Missing {config_path}\n"
            f"Copy {EXAMPLE_CONFIG} to {DEFAULT_CONFIG} and edit your SSH aliases."
        )
    data = json.loads(config_path.read_text())
    hosts: list[HostSpec] = []
    for entry in data.get("hosts", []):
        hosts.append(
            HostSpec(
                alias=entry["ssh_alias"],
                label=entry["label"],
                profile=entry.get("hermes_profile"),
            )
        )
    if not hosts:
        raise SystemExit(f"No hosts defined in {config_path}")
    return hosts


def swift_now() -> float:
    return (datetime.now(UTC) - REF).total_seconds()


def probe(alias: str) -> dict | None:
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", alias, HERMES_PROBE]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return None


def load_existing() -> dict[str, dict]:
    if not CONNECTIONS_PATH.exists():
        return {}
    data = json.loads(CONNECTIONS_PATH.read_text())
    by_key: dict[str, dict] = {}
    for entry in data:
        ssh = entry.get("transport", {}).get("ssh", {})
        alias = ssh.get("alias", "")
        profile = entry.get("hermesProfile") or ""
        by_key[f"{alias}|{profile}"] = entry
    return by_key


def make_connection(alias: str, label: str, profile: str | None, existing: dict | None) -> dict:
    now = swift_now()
    entry = {
        "id": (existing or {}).get("id") or str(uuid.uuid4()).upper(),
        "label": label,
        "transport": {
            "kind": "ssh",
            "ssh": {"alias": alias, "host": "", "user": ""},
        },
        "createdAt": (existing or {}).get("createdAt") or now,
        "updatedAt": now,
    }
    if profile:
        entry["hermesProfile"] = profile
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OS1 connections.json from SSH hosts")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Host list JSON (default: {DEFAULT_CONFIG})",
    )
    args = parser.parse_args()
    hosts = load_hosts(args.config)
    existing = load_existing()
    connections: list[dict] = []
    report: list[str] = []

    for spec in hosts:
        discovered = probe(spec.alias)
        if discovered is None:
            report.append(f"SKIP {spec.alias} ({spec.label}) — SSH unreachable")
            continue

        profiles = discovered.get("profiles") or []
        if spec.profile:
            match = next((p for p in profiles if p.get("name") == spec.profile), None)
            if not match:
                report.append(
                    f"SKIP {spec.alias} profile={spec.profile} — profile not found on host"
                )
                continue
            key = f"{spec.alias}|{spec.profile}"
            connections.append(
                make_connection(spec.alias, spec.label, spec.profile, existing.get(key))
            )
            report.append(f"ADD {spec.label} via {spec.alias}")
            continue

        default = next((p for p in profiles if p.get("name") == "default"), None)
        if default and (default.get("sessions") or default.get("state_db")):
            key = f"{spec.alias}|"
            connections.append(
                make_connection(spec.alias, spec.label, None, existing.get(key))
            )
            report.append(f"ADD {spec.label} via {spec.alias}")
        elif not profiles:
            report.append(f"SKIP {spec.alias} — SSH ok but no Hermes data")
        else:
            report.append(f"SKIP {spec.alias} — default Hermes profile empty")

    OS1_DIR.mkdir(parents=True, exist_ok=True)
    CONNECTIONS_PATH.write_text(json.dumps(connections, indent=2) + "\n")

    print(f"Wrote {len(connections)} connection(s) to {CONNECTIONS_PATH}")
    for line in report:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
