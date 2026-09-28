# Compose setup

## Launcher and secrets

Run the single `homelab` project from this directory, not an included subdirectory.

Authenticate the 1Password CLI first. Keep only secret references in `secrets.env`,
preferably using vault, item, and field IDs.

Mount the homelab's Tailscale Environment locally at `~/tailscale.env` for dashboard
widget credentials. Keep its values machine-local, not in the manifest or repository.

For direct Compose commands, run from this directory:

```powershell
op run --env-file=secrets.env -- docker compose up -d
```

## Tailscale routing

- Create an auth key at
  [Tailscale Console](https://console.tailscale.com/admin/settings/keys)
  and store it in a 1Password vault item.
- Auth key properties:
  - Reusable,
  - ephemeral (optional),
  - pre-approved (optional),
  - tags (`tag:homelab`)

Use the tailnet name without `.ts.net` for `TAILNET_NAME`.
In `tailscale-serve.json`, use `__TAILNET_NAME__` in route hostnames.

```env
# secrets.env (references, never secret values)
TAILNET_NAME="op://<vault-id>/<item-id>/<field-id>"
TS_DOCKER_AUTHKEY="op://<vault-id>/<item-id>/<field-id>"
```

Enable MagicDNS and HTTPS certificates in Tailscale Admin. For each user-facing
route, create a matching Service with endpoint `tcp:443` and `tag:homelab`.
Add `tag:media` only when family should have access. Reserve Service DNS names;
other tailnet devices must not claim them.

## Add a service

Define the app, storage mounts, and `homepage.*` dashboard labels in its Compose
file; include it from `compose.yaml` if needed. For a user-facing app, add its
route in `tailscale-serve.json` and matching Service in Tailscale Admin.
Recreate the gateway after editing routes:

```powershell
op run --env-file=secrets.env -- docker compose up -d --force-recreate homelab-gateway
```
