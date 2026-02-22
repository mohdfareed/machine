# Homelab (macOS)

Always-on Mac as a headless server. Works on MacBook (clamshell), Mac Mini, etc.

## Docker Services

The deploy script creates **real directories** at `~/homelab/<service>/` and
symlinks only `compose.yaml` (and config dirs like `homepage/config/`) from
the repo. Runtime data (`./data/`, logs, `.env`) is written to the real
directory — never into the git repo.

To add a service, drop a directory with a `compose.yaml` under `docker/`.

**Convention:** persistent data goes in `./data/` relative to the compose file.
Secrets go in `.env` (gitignored — manually provisioned or restored from backup).

## Script Prefixes

| Prefix     | When it runs             | Example               |
| ---------- | ------------------------ | --------------------- |
| `init_`    | Before packages          | `init_server`         |
| *(none)*   | After packages           | `docker`, `tailscale` |
| `upgrade_` | Only during `mc upgrade` | `upgrade_server`      |

## Backups

The homelab Mac pulls `~/homelab/*/data/` and `*/.env` from remote servers via
rsync over Tailscale SSH. A launchd job (`com.mc.backup.plist`) runs daily at
04:30 after the 04:00 scheduled wake.

Backups land in iCloud:

```
$MC_PRIVATE/backups/<hostname>/<service>/
├── data/
└── .env
```

Trigger manually: `launchctl kickstart gui/$(id -u)/com.mc.backup` or just
run `~/homelab/../scripts/backup.macos.sh` directly.

Time Machine complements this by covering the homelab Mac's *own* data
automatically (local Docker volumes, configs, etc.).

### Restoring a remote server

After `mc setup <machine>` deploys compose files (but no data):

```sh
# From any machine with iCloud access, push data to the target
BACKUP="$MC_PRIVATE/backups/<hostname>"
for svc in "$BACKUP"/*/; do
    name="$(basename "$svc")"
    scp -r "$svc/data" <host>:~/homelab/"$name"/data 2>/dev/null || true
    scp "$svc/.env" <host>:~/homelab/"$name"/.env 2>/dev/null || true
done
# Then on the target: mc setup <machine>  (redeploys everything)
```

### Moving a service between machines

1. Add the `compose.yaml` to the new machine's `docker/` dir in git
2. Transfer `data/` + `.env` via scp (from backup or old host)
3. `mc setup <machine>` deploys and starts it

## Network

Tailscale provides encrypted SSH and MagicDNS (`ssh homelab`). No port
forwarding or reverse proxy needed.
