# Homelab (macOS)

Always-on Mac used as a headless server. Works on MacBook (clamshell), Mac Mini,
etc.

## Set up

- Mount the [media](./docker/media/README.md) storage before deploying.
- In 1Password, mount the `tailscale` Environment at `~/tailscale.env`.
  Compose reads it directly; no beta CLI is needed.
- Restore any service `data/` backups before starting the apps; otherwise they
  start with fresh configuration.
- Finish Docker Desktop's first launch and Tailscale sign-in. After a reboot,
  check both are running in the logged-in user session; power-on alone isn't enough.
  - Ensure Docker is using gRPC FUSE for volume mounts.
- On a fresh media install, do the [first steps](docker/media/README.md#first-start)
  before the full deployment.

Grant the terminal app Full Disk Access before deploying (required to enable SSH).
After every deployment, complete the Sharing review in the
[shared homelab setup notes](../../config/homelab/README.md).

Run `mc deploy` for the complete machine setup, including Dashboard's Tailscale
HTTPS address. `tailscale serve status` shows that address.
