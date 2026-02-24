# Homelab (macOS)

Always-on Mac as a headless server. Works on MacBook (clamshell), Mac Mini, etc.

## Docker Services

See [config/homelab/README.md](../../config/homelab/README.md) for the
module documentation and how to add or expose services.

## Backups

A launchd job (`com.mc.backup.plist`) runs daily at 04:30 after a 04:00
scheduled wake. It pulls `~/.homelab/*/data/` and `*/.env` from remote
servers (and itself) via rsync over Tailscale SSH.

Backups land in iCloud:

```
$MC_PRIVATE/backups/<hostname>/<service>/
├── data/
└── .env
```

Trigger manually:

```sh
launchctl kickstart gui/$(id -u)/com.mc.backup
```

Time Machine covers the homelab Mac's own data (local Docker volumes,
configs, etc.).

### Restoring a remote server

After `mc setup <machine>` deploys compose files (but no data):

```sh
BACKUP="$MC_PRIVATE/backups/<hostname>"
for svc in "$BACKUP"/*/; do
    name="$(basename "$svc")"
    scp -r "$svc/data" <host>:~/.homelab/"$name"/data 2>/dev/null || true
    scp "$svc/.env" <host>:~/.homelab/"$name"/.env 2>/dev/null || true
done
# Then on the target: mc setup <machine>
```

### Moving a service between machines

1. Add the `compose.yaml` to the new machine's `docker/` dir in git
2. Transfer `data/` + `.env` via scp (from backup or old host)
3. `mc setup <machine>` deploys and starts it

## Network

Tailscale provides encrypted SSH and MagicDNS (`ssh homelab`). No port
forwarding or reverse proxy needed.
