# Homelab (macOS)

Always-on Mac used as a headless server. Works on MacBook (clamshell), Mac Mini,
etc.

## Services

See [config/homelab/README.md](../../config/homelab/README.md) for the
module documentation and how to add or expose services.

See [media services](docker/media/README.md) for the media stack.

## Backups

A launchd job (`com.mc.backup.plist`) runs daily at 04:30. It creates a separate
compressed snapshot for each configured host. Every host uses its own
`MC_HOMELAB_DIR`, falling back to `~/.homelab`, and retains its newest 14
snapshots.

Backups land in iCloud:

```txt
$MC_PRIVATE/backups/<host>/<timestamp>.tar.gz
```

Trigger manually:

```sh
launchctl kickstart gui/$(id -u)/com.mc.backup
```
