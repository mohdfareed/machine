# Compose setup

## Launcher and secrets

Run the single `homelab` project from this directory, not an included subdirectory.

Authenticate the 1Password CLI first. Keep only secret references in `secrets.env`,
preferably using vault, item, and field IDs.

Mount the homelab's Tailscale Environment locally at `~/tailscale.env` for dashboard
widget credentials. Keep its values machine-local, not in the manifest or repository.

For direct Compose commands, run from this directory:

```sh
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
  - tags (`tag:container`)

Use the tailnet name without `.ts.net` for `TAILNET_NAME`.

```env
# secrets.env (references, never secret values)
TAILNET_NAME="op://<vault-id>/<item-id>/<field-id>"
TS_DOCKER_AUTHKEY="op://<vault-id>/<item-id>/<field-id>"
```

Enable MagicDNS and HTTPS certificates in Tailscale Admin. For each user-facing
route, create a matching Service with endpoint `tcp:443` and `tag:homelab`.
Add `tag:media` only when family should have access. Reserve Service DNS names;
other tailnet devices must not claim them.

The gateway **device** uses `tag:container`; `tag:homelab` and `tag:media` belong
to the **Services**. Review `../tailscale.acl.jsonc` before applying the policy.

## Add a service

Define the app, storage mounts, and `homepage.*` dashboard labels in its Compose
file; include it from `compose.yaml` if needed. For a user-facing app, add its
route in `compose.tailscale.yaml` and matching Service in Tailscale Admin.
