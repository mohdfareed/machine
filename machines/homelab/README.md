# Homelab (macOS)

Always-on Mac used as a headless server. Works on MacBook (clamshell), Mac Mini,
etc.

## Services

See [config/homelab/README.md](../../config/homelab/README.md) for the
module documentation and how to add or expose services.

See [media services](docker/media/README.md) for the media stack.
Whisper.cpp runs natively through launchd for Metal-accelerated speech
recognition at the model gateway's `/v1/audio/` path.

## Backups

A launchd job (`com.mc.backup.plist`) runs daily at 04:30. It creates a separate
compressed snapshot for each configured host from its required
`MC_HOMELAB_DIR` and retains its newest 14 snapshots.

Backups land in iCloud:

```txt
$MC_PRIVATE/backups/<host>/<timestamp>.tar.gz
```

Trigger manually:

```sh
launchctl kickstart gui/$(id -u)/com.mc.backup
```
