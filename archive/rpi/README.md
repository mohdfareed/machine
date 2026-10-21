# RPi

Raspberry Pi running as a lightweight Linux server.

Docker services are deployed the same way as on the homelab Mac - the deploy
script creates real directories at `~/.homelab/<service>/` and symlinks compose
files from the repo. Runtime data stays outside the git tree.

Backups are handled by the homelab Mac, which pulls data over Tailscale SSH.
See [homelab/README.md](../homelab/README.md) for restore and migration steps.
