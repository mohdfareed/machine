# Homelab (macOS)

Always-on Mac used as a headless server. Works on MacBook (clamshell), Mac Mini,
etc.

## Docker Services

See [config/homelab/README.md](../../config/homelab/README.md) for the
module documentation and how to add or expose services.

The [media services](docker/media/README.md) run Seerr, the standard Arr
automation stack, SABnzbd, qBittorrent with VueTorrent, and Plex for local
media acquisition, organization, subtitles, and playback.

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
