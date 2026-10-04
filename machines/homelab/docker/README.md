# Compose setup

## Launcher and secrets

Run `mc deploy -m homelab` to deploy each immediate subdirectory containing
`compose.yaml`. Projects share the `homelab` Docker network.

Each project lists its 1Password Environment IDs in `env.txt`, one per line;
later entries take precedence. Optional `secrets.env` files contain vault references.
Direct Environment loading requires the 1Password CLI beta.

A missing service-account token prompts privately and
is saved in `~/.config/machine/credentials/1password-token` with owner-only access.
If secret loading fails, deployment shows the error and offers private token replacement.
Declining or entering nothing leaves the saved token unchanged.
Grant the account access to the selected Environments and referenced vaults.

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
In `gateway/tailscale-serve.json`, use `__TAILNET_NAME__` in route hostnames.

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
file. For a new project, add a subdirectory with `compose.yaml` and `env.txt`
(which may be empty), and join its default network to the external `homelab`
network. Add `secrets.env` only when using vault references. For a user-facing app, add its
route in `gateway/tailscale-serve.json` and matching Service in Tailscale Admin.
Recreate the gateway after editing routes by redeploying machine.