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

Power/sleep and sharing settings are in [init_server.sh](scripts/init_server.sh).

## Backup

Daily at **04:30**, keeping **14 snapshots per host**:

`$MC_HOMELAB_STORAGE_DIR/Backups/<host>/<timestamp>.tar.gz`

```sh
mc::backup --start # start backup
mc::backup         # check status
# log: `/tmp/mc-backup.log`
```
