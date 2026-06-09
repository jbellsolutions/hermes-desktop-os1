#!/usr/bin/env python3
"""Install SSH keys on a DO droplet via noVNC using wget from an HTTP install host.

VNC keyboard mangling rules (DO noVNC canvas):
  ( -> 9, ) -> 0, && -> 77, _ -> - when typing manually
  Use wget without scheme: wget HOST/k.sh
  Always: rm -f k.sh k.sh.1 before wget (wget saves k.sh.1 if k.sh exists)
  Never type install commands directly — only run sh k.sh from HTTP host.

Configure install host in scripts/config/droplets.json or OS1_INSTALL_HOST.

Optional login flow when console shows login prompt (after doctl password-reset).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import browser_cookie3
from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.bootstrap_config import load_install_settings, wget_lines  # noqa: E402

PERM_PRIV = Path.home() / ".ssh/id_ed25519"


def _wget_lines() -> list[str]:
    host, script = load_install_settings()
    return wget_lines(host, script)


def chrome_cookies() -> list[dict]:
    return [
        {
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "secure": bool(c.secure),
        }
        for c in browser_cookie3.chrome(domain_name="digitalocean.com")
    ]


def remote_caps_on(page: Page) -> bool:
    return "Caps Lock on" in page.evaluate("() => document.body.innerText")


def type_char(page: Page, ch: str, caps_on: bool, delay: int = 50) -> None:
    if ch == '"':
        page.keyboard.press("Shift+Quote", delay=delay)
        return
    if "a" <= ch <= "z":
        if caps_on:
            page.keyboard.down("Shift")
            page.keyboard.press(ch.upper(), delay=delay)
            page.keyboard.up("Shift")
        else:
            page.keyboard.press(ch, delay=delay)
    elif "A" <= ch <= "Z":
        if caps_on:
            page.keyboard.press(ch.lower(), delay=delay)
        else:
            page.keyboard.down("Shift")
            page.keyboard.press(ch.lower(), delay=delay)
            page.keyboard.up("Shift")
    else:
        page.keyboard.type(ch, delay=delay)


def type_line(page: Page, text: str, caps_on: bool, wait: int = 15000) -> None:
    page.keyboard.type(text, delay=40)
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    page.wait_for_timeout(wait)


def prepare_console(page: Page) -> bool:
    page.evaluate(
        """() => {
      const c = document.getElementById('noVNC_canvas');
      if (!c) return;
      c.style.pointerEvents = 'auto';
      c.style.height = '600px';
      c.style.width = '100%';
    }"""
    )
    page.wait_for_timeout(800)
    page.locator("#noVNC_canvas").click(position={"x": 220, "y": 200})
    page.wait_for_timeout(1200)
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    return remote_caps_on(page)


def login_lines(root_pass: str, new_pass: str | None) -> tuple[list[str], list[int]]:
    lines = ["root", root_pass]
    waits = [8000, 12000]
    if new_pass:
        lines.extend([root_pass, new_pass, new_pass])
        waits.extend([8000, 8000, 8000])
    return lines, waits


def bootstrap_console(
    page: Page, caps_on: bool, root_pass: str | None, new_pass: str | None, skip_login: bool
) -> bool:
    if root_pass and not skip_login:
        type_line(page, "root", caps_on, 8000)
        caps_on = remote_caps_on(page)
        type_line(page, root_pass, caps_on, 15000)
        caps_on = remote_caps_on(page)
        if new_pass:
            type_line(page, root_pass, caps_on, 10000)
            caps_on = remote_caps_on(page)
            type_line(page, new_pass, caps_on, 10000)
            caps_on = remote_caps_on(page)
            type_line(page, new_pass, caps_on, 12000)
            caps_on = remote_caps_on(page)
    for line in _wget_lines():
        type_line(page, line, caps_on, 25000)
        caps_on = remote_caps_on(page)
    return True


def fetch_reset_password(droplet_name: str, wait_seconds: int = 0, retries: int = 5) -> str | None:
    if wait_seconds:
        time.sleep(wait_seconds)
    pattern = (
        rf"\({re.escape(droplet_name)}\)[\s\S]{{0,400}}?"
        r"temporarily reset to:\s*([a-f0-9]{{20,40}})"
    )
    cookies = [
        {
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "secure": bool(c.secure),
        }
        for c in browser_cookie3.chrome(domain_name="google.com")
    ]
    queries = [
        f"from:digitalocean \"({droplet_name})\" newer_than:1d",
        f"from:digitalocean {droplet_name} temporarily reset",
        f"from:digitalocean \"({droplet_name})\" password reset",
        "from:digitalocean password has been reset newer_than:1d",
    ]
    for attempt in range(retries):
        if attempt:
            time.sleep(12)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            ctx.add_cookies(cookies)
            page = ctx.new_page()
            for query in queries:
                page.goto(
                    f"https://mail.google.com/mail/u/0/#search/{query.replace(' ', '+')}",
                    wait_until="domcontentloaded",
                    timeout=180_000,
                )
                page.wait_for_timeout(10_000)
                text = page.evaluate("() => document.body.innerText")
                block = re.search(pattern, text, re.IGNORECASE)
                if block:
                    browser.close()
                    return block.group(1)
            browser.close()
    return None


def run_wget_install(page: Page, caps_on: bool) -> None:
    lines = _wget_lines()
    if run_lines_rfb(page, lines, [22000, 22000, 28000]):
        return
    for line in lines:
        type_line(page, line, caps_on, 22000)


RFB_TYPE_JS = """
async ({ lines, waits }) => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 120; i++) {
    const rfb = window.rfb;
    const state = rfb && (rfb._rfb_connection_state || rfb._rfb_state);
    if (state === "connected" || state === "normal") break;
    await sleep(500);
  }
  const rfb = window.rfb;
  if (!rfb) return false;
  const tap = (keysym) => {
    rfb.sendKey(keysym, null, true);
    rfb.sendKey(keysym, null, false);
  };
  const typeText = async (text, delay = 70) => {
    for (const ch of text) {
      tap(ch.charCodeAt(0));
      await sleep(delay);
    }
  };
  const enter = async () => {
    tap(0xff0d);
    await sleep(500);
  };
  const canvas = document.getElementById("noVNC_canvas");
  if (canvas) {
    canvas.style.pointerEvents = "auto";
    canvas.style.height = "600px";
    canvas.click();
  }
  await sleep(1500);
  for (let i = 0; i < lines.length; i++) {
    await typeText(lines[i]);
    await enter();
    await sleep(waits[i] || 15000);
  }
  return true;
}
"""


def run_lines_rfb(page: Page, lines: list[str], waits: list[int]) -> bool:
    try:
        return bool(page.evaluate(RFB_TYPE_JS, {"lines": lines, "waits": waits}))
    except Exception:
        return False


def verify_ssh(ip: str, user: str = "root") -> bool:
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
            f"{user}@{ip}",
            "echo SSH_OK",
        ],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and "SSH_OK" in proc.stdout


def verify_ssh_any(ip: str) -> tuple[bool, str | None]:
    for user in ("root", "claw"):
        if verify_ssh(ip, user):
            return True, user
    return False, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap DO droplet SSH via noVNC wget")
    parser.add_argument("--droplet-id", type=int, required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--root-pass", help="Temp root password after DO password reset")
    parser.add_argument(
        "--droplet-name",
        help="Droplet name for Gmail password lookup (with --fetch-pass)",
    )
    parser.add_argument(
        "--fetch-pass",
        action="store_true",
        help="Read latest DO reset password from Gmail via Chrome cookies",
    )
    parser.add_argument("--new-pass", default="Os1Bootstrap2026Xy")
    parser.add_argument(
        "--no-new-pass",
        action="store_true",
        help="Do not force password change after login (pubkey-only droplets)",
    )
    parser.add_argument("--skip-login", action="store_true", help="Skip console login (already at shell)")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--screenshot", default="/tmp/vnc-wget-bootstrap.png")
    args = parser.parse_args()

    root_pass = args.root_pass
    if args.fetch_pass:
        if not args.droplet_name:
            print("--fetch-pass requires --droplet-name", file=sys.stderr)
            return 1
        time.sleep(45)
        root_pass = fetch_reset_password(args.droplet_name)
        if not root_pass:
            print(f"No reset password found in Gmail for {args.droplet_name}", file=sys.stderr)
            return 1
        print(f"Gmail reset password for {args.droplet_name}: {root_pass}")

    cookies = chrome_cookies()
    if not cookies:
        print("No Chrome DO cookies", file=sys.stderr)
        return 1

    url = f"https://cloud.digitalocean.com/droplets/{args.droplet_id}/console"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=180_000)
        page.wait_for_timeout(28_000)
        caps_on = prepare_console(page)
        print(f"remote caps on: {caps_on}")
        new_pass = None if args.no_new_pass else args.new_pass
        if root_pass and not args.skip_login:
            print(f"Bootstrapping via keyboard login + wget (new_pass={'yes' if new_pass else 'no'})")
        bootstrap_console(page, caps_on, root_pass, new_pass, args.skip_login)
        page.screenshot(path=args.screenshot, full_page=True)
        browser.close()

    time.sleep(3)
    ok, user = verify_ssh_any(args.ip)
    if ok:
        print(f"SSH OK {user}@{args.ip}")
        return 0
    print(f"SSH FAIL root|claw@{args.ip}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
