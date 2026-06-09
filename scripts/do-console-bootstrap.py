#!/usr/bin/env python3
"""Bootstrap SSH via DigitalOcean web console session (Chrome cookies)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import browser_cookie3
from playwright.sync_api import sync_playwright

DROPLET_ID = 567676939
DROPLET_IP = "104.236.11.200"
PERM_PUB = Path.home() / ".ssh/id_ed25519.pub"
CONSOLE_URL = f"https://cloud.digitalocean.com/droplets/{DROPLET_ID}/console"


def chrome_cookies() -> list[dict]:
    jar = browser_cookie3.chrome(domain_name="digitalocean.com")
    out = []
    for c in jar:
        out.append(
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path or "/",
                "secure": bool(c.secure),
                "httpOnly": bool(getattr(c, "_rest", {}).get("HttpOnly", False)),
            }
        )
    return out


def gen_ephemeral_key(tmp: Path) -> tuple[Path, Path]:
    priv = tmp / "console_ephemeral"
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-f", str(priv), "-N", "", "-C", "os1-console-bootstrap"],
        check=True,
        capture_output=True,
    )
    return priv, Path(str(priv) + ".pub")


def install_perm_key(ephemeral_priv: Path) -> None:
    pubkey = PERM_PUB.read_text().strip()
    remote = (
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
        f"grep -qF '{pubkey}' ~/.ssh/authorized_keys 2>/dev/null || "
        f"echo '{pubkey}' >> ~/.ssh/authorized_keys && "
        "chmod 600 ~/.ssh/authorized_keys && echo OS1_KEY_INSTALLED"
    )
    cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "IdentitiesOnly=yes",
        "-i",
        str(ephemeral_priv),
        f"root@{DROPLET_IP}",
        remote,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"ssh install failed: {proc.stderr or proc.stdout}")
    if "OS1_KEY_INSTALLED" not in proc.stdout:
        raise RuntimeError(f"unexpected ssh output: {proc.stdout}")


def main() -> int:
    cookies = chrome_cookies()
    if not cookies:
        print("No digitalocean.com cookies in Chrome", file=sys.stderr)
        return 1

    captured: list[dict] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        priv, pub = gen_ephemeral_key(tmp)
        pub_text = pub.read_text().strip()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()

            def on_request(req):
                url = req.url
                if any(
                    s in url
                    for s in (
                        "console",
                        "dotty",
                        "ssh",
                        "droplet-agent",
                        "metadata",
                        "terminal",
                    )
                ):
                    body = None
                    try:
                        body = req.post_data
                    except Exception:
                        pass
                    captured.append({"url": url, "method": req.method, "body": body})

            def on_response(resp):
                url = resp.url
                if any(
                    s in url
                    for s in ("console", "dotty", "ssh", "droplet-agent", "terminal")
                ):
                    try:
                        text = resp.text()
                    except Exception:
                        text = ""
                    captured.append(
                        {
                            "url": url,
                            "status": resp.status,
                            "response": text[:2000],
                        }
                    )

            page.on("request", on_request)
            page.on("response", on_response)

            page.goto(CONSOLE_URL, wait_until="networkidle", timeout=120_000)
            time.sleep(8)

            # Try posting pubkey to any discovered register endpoints
            api_calls = []
            for item in captured:
                url = item.get("url", "")
                if item.get("method") == "POST" and "digitalocean" in url:
                    api_calls.append(item)

            (tmp / "network_log.json").write_text(json.dumps(captured, indent=2))
            print(f"Captured {len(captured)} network events -> {tmp / 'network_log.json'}")

            browser.close()

        # Wait for droplet-agent to install dotty key
        for attempt in range(12):
            probe = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=5",
                    "-o",
                    "IdentitiesOnly=yes",
                    "-i",
                    str(priv),
                    f"root@{DROPLET_IP}",
                    "echo CONSOLE_OK",
                ],
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0 and "CONSOLE_OK" in probe.stdout:
                print("Ephemeral console SSH works")
                install_perm_key(priv)
                print("Permanent mac-os1 key installed")
                return 0
            time.sleep(5)

        print("Console page opened but ephemeral SSH never worked", file=sys.stderr)
        print(f"Ephemeral pubkey was:\n{pub_text}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
