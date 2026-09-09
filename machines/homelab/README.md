# Homelab (macOS)

Always-on Mac used as a headless server. Works on MacBook (clamshell), Mac Mini,
etc.

## Set up

- Download the private env from iCloud (or any cloud service),
  and mount the [media](./docker/media/README.md) storage before deploying.
- Restore any service `data/` backups before starting the apps; otherwise they
  start with fresh configuration.
- Finish Docker Desktop's first launch and Tailscale sign-in. After a reboot,
  check both are running in the logged-in user session; power-on alone isn't enough.
- Select this machine with `mc apply -m homelab`. On a fresh media install, do the
  [first-start steps](docker/media/README.md#first-start) before the full deployment.

Power/sleep and file sharing setup are in [init_server.sh](scripts/init_server.sh).
Once per installation, in System Settings

- Grant the terminal app Full Disk Access before applying (required to enable SSH).
- Under General → Sharing → Remote Login, verify only Administrators have access;
  setup preserves existing memberships. Enable remote-user Full Disk Access if needed.
- Enable Remote Management for your account and choose its privileges and menu-bar
  options. Set a VNC password only if your client needs legacy VNC.
- Under File Sharing, choose shared folders and permissions, enable your account
  under Options → Windows File Sharing. NOTE: You must provide Full Disk Access.
  Configure the Time Machine backup-destination option on its share if used.

## Backup

Daily at **04:30**, keeping **14 snapshots per host**:
`$MC_HOMELAB_STORAGE_DIR/Backups/<host>/<timestamp>.tar.gz`

```sh
mc::backup # start backup
# log: `/tmp/mc-backup.log`
```

For backups to the external drive, enable `/bin/zsh` in **System Settings →
Privacy & Security → Full Disk Access**. Without this, scheduled backups can
fail with `Operation not permitted`.
