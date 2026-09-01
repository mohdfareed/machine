# Media

Scryer organizes media, qBittorrent downloads it, VueTorrent provides the
torrent interface, and Plex streams it to clients. Homepage discovers Scryer,
Torrents, and Plex through their Compose labels.

## Access

Each UI has a dedicated private Tailscale hostname and no published web port:

| Service               | Address                                      |
| --------------------- | -------------------------------------------- |
| Scryer                | `https://scryer.<tailnet>.ts.net`            |
| Torrents (VueTorrent) | `https://qbittorrent.<tailnet>.ts.net`       |
| Plex                  | `https://plex.<tailnet>.ts.net/web`          |

The Apple TV must be connected to the tailnet. Funnel is disabled for every
service. qBittorrent's peer port is the only published host port. Its web
server listens only on loopback inside the Tailscale sidecar's network
namespace.

## Storage

Application state follows the normal service convention and is included in the
homelab backup:

```txt
~/.homelab/media/data/{scryer,qbittorrent,plex}
```

Bulk data stays outside `data/` so it is not copied into the daily iCloud
backup. `HOMELAB_MEDIA_DIR` currently expands to
`~/.homelab/storage/media`:

```txt
downloads/
movies/
series/
anime/
transcode/
```

The `init_media.unix.sh` script creates these directories automatically during
`mc apply`; no manual `mkdir` step is required. Scryer and qBittorrent mount
the parent read-write at `/data`, while Plex mounts it read-only. Keeping
downloads and libraries below one mount lets Scryer hard-link imports without
duplicating their contents.

Change only `HOMELAB_MEDIA_DIR` in `machines/homelab/machine.env` when moving
bulk data to an external drive.

## First Run

1. Open Torrents. VueTorrent is already enabled, the save path is
   `/data/downloads`, and Tailscale Serve's loopback connection bypasses the
   qBittorrent login.
2. Open Scryer. It starts loginless as its built-in full administrator; no
   recovery password or first-run account is required. Configure
   `/data/downloads`, `/data/movies`, `/data/series`, and `/data/anime`. Add
   qBittorrent as `https://qbittorrent.<tailnet>.ts.net`; no qBittorrent
   credentials are required.
3. Open Plex, claim the server, and add `/data/movies`, `/data/series`, and
   `/data/anime` as libraries.

The login bypasses apply only to loopback requests from Tailscale Serve.
Scryer's Serve endpoint terminates TLS and forwards the connection without HTTP
proxy headers because Scryer intentionally rejects loginless requests carrying
a Tailscale `100.64.0.0/10` client address. Host header, CSRF, and clickjacking
protections remain enabled for qBittorrent, and its allowed server domain is
limited to `qbittorrent.<tailnet>.ts.net`.

Tailnet policy is the access boundary: every identity allowed to reach Scryer
is a full administrator, so only trusted users should be allowed to reach the
Scryer and qBittorrent nodes.

qBittorrent remains the download engine and WebAPI used by Scryer; VueTorrent
only replaces its browser interface. The derived image pins VueTorrent 2.35.0
and verifies the release archive checksum during the build.

Existing Scryer installations must replace `http://ts-qbittorrent:8080` with
the HTTPS tailnet address above; the direct container URL intentionally stops
working when qBittorrent binds to loopback. The startup wrapper reapplies the
VueTorrent, loopback, authentication, domain, and download-path settings on
every container start, so changes to those managed settings in the UI do not
persist.

The qBittorrent container sets `QBT_LEGAL_NOTICE=confirm`, as required by the
official image. Use it only for content you are authorized to download and
share.
