# Homelab deployment

A homelab is a personal server setup for self-hosting Docker services.
The dashboard uses the host's Tailscale HTTPS address;
`tailscale serve status` shows it.

Installs Docker (Linux) and Tailscale, deploys services, and configures
Tailscale networking.

[macOS setup](../../machines/homelab/README.md) ·
[Media setup](../../machines/homelab/docker/media/README.md)

## Tailscale

- Create Auth and API keys at
  [Tailscale Console](https://console.tailscale.com/admin/settings/keys)
  and store them in `$MC_PRIVATE/env/$MC_ID.env` below.
- Auth key properties:
  - Reusable,
  - ephemeral (optional),
  - pre-approved (optional),
  - tags (`tag:container`)

```env
# `$MC_PRIVATE/env/$MC_ID.env`
TAILNET_NAME=<tailnet-name-without-.ts.net>
TAILSCALE_API_KEY=tskey-api-<id>-<secret>
TS_DOCKER_AUTHKEY=tskey-client-<id>-<secret>
```

After starting containers, approve their devices in
[Tailscale Machines](https://login.tailscale.com/admin/machines) if not pre-
approved to allow cross-container communication.

Add to the [tailnet policy](https://login.tailscale.com/admin/acls):

```jsonc
"tagOwners": { "tag:container": ["autogroup:admin"] },
"nodeAttrs": [{ "target": ["tag:container"], "attr": ["funnel"] }]
"grants": [
    {
        "src": ["tag:container"],
        "dst": ["tag:container"],
        "ip": ["tcp:443"],
    },
],
```

**Note:** Funnel is enabled per container/service. each service's
`AllowFunnel` in `serve.json` decides whether to use it.

> Example ACLs configuration at [`tailscale.acl.jsonc`](./tailscale.acl.jsonc).

### Networking

Services are exposed via Tailscale at `service-name.<tailnet>.ts.net`
using one of three patterns:

| Pattern               | How                                        | Example    |
| --------------------- | ------------------------------------------ | ---------- |
| **Internet (funnel)** | Tailscale sidecar with `AllowFunnel: true` | Public app |
| **Tailnet only**      | Host loopback port + `tailscale serve`     | Homepage   |
| **Internal**          | No sidecar, no ports - container-only      | Worker bot |

## Docker

Docker is automatically installed, but should be started for the first time and
configured to run on boot.

The deploy script (`docker.unix.sh`) creates `~/.homelab/<service>/`
directories on the host, symlinks compose files from the repo, and runs
`docker compose up`. Runtime data (volumes, logs) stays in `~/.homelab/` for
manual backup and migration. Example backup script at
[`_backup.sh`](../../machines/homelab/scripts/_backup.sh).

### Add a service

Create a `<service>/compose.yaml` file per service at:

- `machines/<id>/docker/`; or
- `config/homelab/docker/` for shared services (for multiple deployments).

```mermaid
flowchart TD
    Shared["config/homelab/docker/service"] --> Deploy["mc deploy homelab"]
    Machine["machines/id/docker/service"] --> Deploy
    Deploy --> Link["~/.homelab/service → repo"]
    Link --> Compose["Docker Compose"]
```

### Deploy or update

Run on the target machine, with `homelab` included in its manifest:

```sh
mc deploy homelab
```

This pulls/builds and starts **all** its Compose stacks.
For an individual service, open its directory under `~/.homelab/`:

```sh
secrets # alias to load private env vars
docker compose up -d --build
docker compose logs --follow
```
