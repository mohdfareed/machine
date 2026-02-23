"""Homelab Docker service deployment module.

Sources:
  1. config/homelab/docker/  — shared services (traefik, watchtower)
  2. machines/<id>/docker/   — machine-specific services (portainer, openclaw, etc.)

Creates real directories at ~/.homelab/<service>/ and symlinks compose.yaml
(and config dirs) from the repo. Runtime data (./data/, logs) is written
into the real directory — never into the git repo.

Env vars: Each compose file declares its env vars via `environment:` with
${VAR} references. Docker Compose resolves them from the shell environment
(sourced from ~/.env below). No per-service .env files needed.

Configures Tailscale for homelab use.
Sets up serve → Traefik (tailnet-only HTTPS).
Machine-specific scripts can add funnel routes on top.
Set MC_HOMELAB_TUNNEL to also configure the Tailscale Funnel (public HTTPS).

Traefik handles all path routing internally.
  serve (:443) → Traefik :8080 (private, tailnet-only)
"""

from machine.manifest import Module

module = Module()
