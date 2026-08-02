# Homelab Module

Docker Compose service deployment with Tailscale networking.

Installs Docker (Linux) and Tailscale, deploys services from both the shared
module directory and the machine-specific directory, and configures Tailscale
networking.

## How It Works

The deploy script (`docker.unix.sh`) creates `~/.homelab/<service>/`
directories on the host, symlinks compose files from the repo, and runs
`docker compose up`. Runtime data (volumes, logs) stays in `~/.homelab/`
and is never committed to git.

```txt
Sources                              Deployed to
config/homelab/docker/<svc>/   ─┐
                                ├──▸  ~/.homelab/<svc>/  (symlinks)
machines/<id>/docker/<svc>/    ─┘
```

Machine-specific services (Homepage, OpenClaw, KBM, etc.) go in
`machines/<id>/docker/`.

Secrets flow through `~/.env` (built by the shell module) and optionally
`MC_PRIVATE/docker/<service>.env` for service-specific vars. See the
main README's secrets section for the full concatenation flow.

## Networking

Services are exposed via Tailscale using one of three patterns:

| Pattern               | How                                        | Example   |
| --------------------- | ------------------------------------------ | --------- |
| **Internet (funnel)** | Tailscale sidecar with `AllowFunnel: true` | OpenClaw  |
| **Tailnet only**      | Host loopback port + `tailscale serve`     | Homepage  |
| **Internal**          | No sidecar, no ports - container-only      | KBM, bots |

Internet-facing services each get their own tailnet hostname via a sidecar
container (e.g. `openclaw.<tailnet>.ts.net`). Tailnet-only services bind to
a host loopback port and are proxied by the machine's `tailscale serve`.
Internal services have no outside access at all.

## Setup

### 1. Tailscale ACL

Add to your [tailnet policy](https://login.tailscale.com/admin/acls):

```jsonc
"tagOwners": { "tag:container": ["autogroup:admin"] },
"nodeAttrs": [{ "target": ["tag:container"], "attr": ["funnel"] }]
```

The `funnel` attribute grants the **capability** - each service's
`AllowFunnel` in `serve.json` decides whether to use it.

### 2. OAuth Client

Generate at <https://login.tailscale.com/admin/settings/oauth>:

- Scope: **Auth Keys: Write**
- Tag: `tag:container`

### 3. Secrets

Add to `MC_PRIVATE/machine.env` (or `<MC_ID>.env`):

```sh
TS_DOCKER_AUTHKEY=tskey-client-<id>-<secret>?ephemeral=false
TAILNET_NAME=<your-tailnet>
```

| Variable            | Used by                               | Purpose                                                     |
| ------------------- | ------------------------------------- | ----------------------------------------------------------- |
| `TS_DOCKER_AUTHKEY` | Tailscale sidecar containers          | OAuth auth key with `?ephemeral=false` for persistent nodes |
| `TAILNET_NAME`      | Compose files referencing the tailnet | Your tailnet name from admin console                        |

Service-specific secrets go in `MC_PRIVATE/docker/<service>.env`.

## Adding a Service

1. Create `machines/<id>/docker/<name>/compose.yaml`
2. Run `mc apply <machine>` - the deploy script syncs and starts it

### Internet-facing (Tailscale sidecar + funnel)

Add a Tailscale sidecar container and a `ts-config/serve.json`:

```yaml
services:
  ts-myservice:
    image: tailscale/tailscale:latest
    hostname: myservice # <- tailnet hostname
    environment:
      TS_AUTHKEY: ${TS_DOCKER_AUTHKEY}
      TS_EXTRA_ARGS: --advertise-tags=tag:container
      TS_SERVE_CONFIG: /config/serve.json
      TS_STATE_DIR: /var/lib/tailscale
      TS_USERSPACE: "false"
    volumes:
      - ts-state:/var/lib/tailscale
      - ./ts-config:/config
    devices: [/dev/net/tun:/dev/net/tun]
    cap_add: [net_admin]
    restart: unless-stopped

  myservice:
    image: ...
    network_mode: service:ts-myservice
    depends_on: [ts-myservice]

volumes:
  ts-state:
```

`ts-config/serve.json` (set `AllowFunnel` to `false` for tailnet-only):

```json
{
  "TCP": { "443": { "HTTPS": true } },
  "Web": {
    "${TS_CERT_DOMAIN}:443": {
      "Handlers": { "/": { "Proxy": "http://127.0.0.1:<PORT>" } }
    }
  },
  "AllowFunnel": { "${TS_CERT_DOMAIN}:443": true }
}
```

### Tailnet-only (host port + tailscale serve)

Bind to loopback and add a `tailscale serve` call in `tailscale.unix.sh`:

```yaml
ports:
  - 127.0.0.1:<PORT>:<PORT>
```

```sh
sudo tailscale serve --bg --set-path /<path> http://127.0.0.1:<PORT>
```

### Internal only

No ports, no sidecar. Only reachable by containers in the same compose file.
