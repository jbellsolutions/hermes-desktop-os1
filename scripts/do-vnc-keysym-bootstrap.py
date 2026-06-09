#!/usr/bin/env python3
"""Bootstrap SSH on DO droplet via noVNC using explicit RFB keysyms (caps-safe)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import browser_cookie3
from playwright.sync_api import sync_playwright

PERM_PUB = Path.home() / ".ssh/id_ed25519.pub"
PERM_PRIV = Path.home() / ".ssh/id_ed25519"

TYPE_JS = """
async (lines) => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const rfb = window.rfb;
  if (!rfb) throw new Error("no rfb");
  for (let i = 0; i < 80; i++) {
    const state = rfb._rfb_connection_state || rfb._rfb_state;
    if (state === "connected" || state === "normal") break;
    await sleep(500);
  }
  const canvas = document.getElementById("noVNC_canvas");
  if (canvas) {
    canvas.style.pointerEvents = "auto";
    canvas.style.height = "600px";
    canvas.style.width = "100%";
    canvas.click();
  }
  const tap = (keysym) => {
    rfb.sendKey(keysym, null, true);
    rfb.sendKey(keysym, null, false);
  };
  const typeText = async (text, delay = 90) => {
    for (const ch of text) {
      tap(ch.charCodeAt(0));
      await sleep(delay);
    }
  };
  const enter = async () => {
    tap(0xff0d);
    await sleep(400);
  };
  await sleep(1000);
  tap(0xff0d);
  await sleep(1500);
  tap(0xffe9);
  await sleep(800);
  for (const line of lines) {
    await typeText(line);
    await enter();
    const wait = line === "root" ? 6000 : line.startsWith("mkdir") ? 12000 : 7000;
    await sleep(wait);
  }
  return "done";
}
"""


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--droplet-id", type=int, default=567676939)
    parser.add_argument("--ip", default="104.236.11.200")
    parser.add_argument("--root-pass", default="c52fd16e7e8c1e282f830c4941")
    args = parser.parse_args()

    pubkey = PERM_PUB.read_text().strip()
    install = (
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
        f"grep -qF '{pubkey}' ~/.ssh/authorized_keys 2>/dev/null || "
        f"echo '{pubkey}' >> ~/.ssh/authorized_keys && "
        "chmod 600 ~/.ssh/authorized_keys && echo OS1_KEY_INSTALLED"
    )

    cookies = chrome_cookies()
    if not cookies:
        print("No Chrome DO cookies", file=sys.stderr)
        return 1

    lines = [
        "root",
        args.root_pass,
        args.root_pass,
        args.root_pass,
        args.root_pass,
        install,
    ]
    url = f"https://cloud.digitalocean.com/droplets/{args.droplet_id}/console"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=120_000)
        page.wait_for_timeout(22_000)
        page.evaluate(TYPE_JS, lines)
        page.wait_for_timeout(5_000)
        page.screenshot(path="/tmp/vnc-keysym-final.png", full_page=True)
        browser.close()

    time.sleep(2)
    if verify_ssh(args.ip):
        print(f"SSH OK root@{args.ip}")
        return 0
    print(f"SSH still failing root@{args.ip}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
