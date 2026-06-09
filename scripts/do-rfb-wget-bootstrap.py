#!/usr/bin/env python3
"""Reset DO root password, fetch from Gmail, run RFB noVNC wget bootstrap."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import browser_cookie3
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.bootstrap_config import load_install_settings, wget_lines  # noqa: E402

PERM_PRIV = Path.home() / ".ssh/id_ed25519"

RFB_JS = """
async ({ lines, waits }) => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 120; i++) {
    const rfb = window.rfb;
    const state = rfb && (rfb._rfb_connection_state || rfb._rfb_state);
    if (state === 'connected' || state === 'normal') break;
    await sleep(500);
  }
  const rfb = window.rfb;
  if (!rfb) throw new Error('no rfb');
  const tap = (keysym) => { rfb.sendKey(keysym, null, true); rfb.sendKey(keysym, null, false); };
  const typeText = async (text, delay = 70) => { for (const ch of text) { tap(ch.charCodeAt(0)); await sleep(delay); } };
  const enter = async () => { tap(0xff0d); await sleep(500); };
  const canvas = document.getElementById('noVNC_canvas');
  if (canvas) { canvas.style.pointerEvents='auto'; canvas.style.height='600px'; canvas.click(); }
  await sleep(1500);
  for (let i = 0; i < lines.length; i++) {
    await typeText(lines[i]);
    await enter();
    await sleep(waits[i] || 15000);
  }
  return 'done';
}
"""


def chrome_cookies(domain: str) -> list[dict]:
    return [
        {
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "secure": bool(c.secure),
        }
        for c in browser_cookie3.chrome(domain_name=domain)
    ]


def fetch_reset_password(droplet_name: str) -> str | None:
    import importlib.util

    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("w", root / "do-vnc-wget-bootstrap.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.fetch_reset_password(droplet_name)


def reset_password(droplet_id: int) -> None:
    proc = subprocess.run(
        ["doctl", "compute", "droplet-action", "password-reset", str(droplet_id), "--format", "ID"],
        capture_output=True,
        text=True,
        check=True,
    )
    action_id = proc.stdout.strip().splitlines()[-1]
    for _ in range(30):
        status = subprocess.run(
            [
                "doctl",
                "compute",
                "action",
                "get",
                action_id,
                "--format",
                "Status",
                "--no-header",
            ],
            capture_output=True,
            text=True,
        )
        if "completed" in status.stdout.lower():
            return
        time.sleep(2)
    time.sleep(15)


def verify_ssh(ip: str) -> bool:
    proc = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=15",
            "-o",
            "IdentitiesOnly=yes",
            "-i",
            str(PERM_PRIV),
            f"root@{ip}",
            "echo SSH_OK",
        ],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and "SSH_OK" in proc.stdout


def bootstrap(droplet_id: int, ip: str, root_pass: str, new_pass: str | None) -> None:
    install_host, install_script = load_install_settings()
    lines = ["root", root_pass]
    waits = [8000, 10000]
    if new_pass:
        lines.extend([root_pass, new_pass, new_pass])
        waits.extend([7000, 7000, 7000])
    lines.extend(wget_lines(install_host, install_script))
    waits.extend([15000, 22000, 28000])

    cookies = chrome_cookies("digitalocean.com")
    url = f"https://cloud.digitalocean.com/droplets/{droplet_id}/console"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=180_000)
        page.wait_for_timeout(25_000)
        page.evaluate(RFB_JS, {"lines": lines, "waits": waits})
        page.screenshot(path=f"/tmp/vnc-rfb-{droplet_id}.png", full_page=True)
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--droplet-id", type=int, required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--droplet-name", required=True)
    parser.add_argument("--new-pass", default="Os1Bootstrap2026Xy")
    parser.add_argument("--no-new-pass", action="store_true")
    parser.add_argument("--skip-reset", action="store_true")
    args = parser.parse_args()

    if not args.skip_reset:
        print(f"Resetting password for {args.droplet_name}...")
        reset_password(args.droplet_id)
        time.sleep(20)

    root_pass = fetch_reset_password(args.droplet_name)
    if not root_pass:
        print("Gmail password not found", file=sys.stderr)
        return 1
    print(f"Using Gmail password: {root_pass}")

    new_pass = None if args.no_new_pass else args.new_pass
    bootstrap(args.droplet_id, args.ip, root_pass, new_pass)
    time.sleep(3)
    if verify_ssh(args.ip):
        print(f"SSH OK root@{args.ip}")
        return 0
    print(f"SSH FAIL root@{args.ip}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
