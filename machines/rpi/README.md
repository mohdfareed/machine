# RPi

Raspberry Pi running as a lightweight Linux server.

Docker services are deployed the same way as on the homelab Mac — each
subdirectory of `docker/` is symlinked to `~/homelab/<service>/` and
auto-deployed by `mc setup rpi`.

Backups are handled by the homelab Mac, which pulls data over Tailscale SSH.
See [homelab/README.md](../homelab/README.md) for restore and migration steps.
