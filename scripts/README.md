# OS1 operator scripts

Helper scripts for building OS1, syncing multi-host SSH connections into the app, and bootstrapping SSH on DigitalOcean droplets when console access is the only path in.

## Quick start

```sh
# Build and install to /Applications
./scripts/rebuild-and-install.sh

# Copy examples, then edit with your SSH aliases and droplets
cp scripts/config/hosts.example.json scripts/config/hosts.json
cp scripts/config/droplets.example.json scripts/config/droplets.json

# Regenerate ~/Library/Application Support/OS1/connections.json
python3 scripts/sync-os1-connections.py

# Probe DO droplets for SSH + Hermes (reads scripts/config/droplets.json)
./scripts/probe-do-hermes.sh
```

## Connection sync

`sync-os1-connections.py` SSH-probes each host in `scripts/config/hosts.json`, detects Hermes profiles on disk, and writes `connections.json` for OS1.

Each host entry:

| Field | Meaning |
|-------|---------|
| `ssh_alias` | `Host` name from `~/.ssh/config` |
| `label` | Display name in OS1 |
| `hermes_profile` | Profile folder under `~/.hermes/profiles/`; omit for default profile |

Use `--config path/to/hosts.json` for a non-default file.

## DigitalOcean VNC bootstrap

When a droplet has no SSH key yet, these scripts drive the DO web console (noVNC) with Playwright:

| Script | Role |
|--------|------|
| `do-vnc-wget-bootstrap.py` | Primary path: `wget` install script from HTTP host, run `sh k.sh` |
| `do-vnc-bootstrap.py` | Thin wrapper → `do-vnc-wget-bootstrap.py` |
| `bootstrap-do-ssh-access.sh` | Single-droplet helper |
| `bootstrap-do-hermes-droplets.sh` | Batch run from `droplets.json` |

**Requirements:** `doctl` (authenticated), Chrome cookies for `digitalocean.com`, `uv` or pip with `playwright` and `browser_cookie3`. Run `playwright install chromium` once.

Set `install_host` in `scripts/config/droplets.json` to the machine that serves your `k.sh` over plain HTTP (no `https://` in the VNC console — colons break typing).

Environment override: `OS1_INSTALL_HOST=203.0.113.1`

### noVNC typing rules (DigitalOcean console)

- Parentheses map oddly: `(` → `9`, `)` → `0`
- Avoid typing URLs with a scheme; use `wget HOST/k.sh` not `wget http://...`
- Always `rm -f k.sh k.sh.1` before wget (stale file becomes `k.sh.1`)

## Other scripts

| Script | Purpose |
|--------|---------|
| `verify-remote-discovery.sh` | Smoke-check remote Hermes discovery |
| `install-os1-key-on-droplet.sh` | Push local pubkey when SSH already works |
| `build-macos-app.sh` | Release build → `dist/OS1.app` |
| `package-github-release.sh` | Zip for GitHub Releases |

## Security

- Never commit `scripts/config/hosts.json` or `droplets.json` with real IPs if the repo is public.
- `k.sh` on your install host should only install **your** SSH public keys.
- Example configs use documentation IPs (`203.0.113.x`).
