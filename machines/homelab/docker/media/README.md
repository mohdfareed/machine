# Media

Scryer organizes media, qBittorrent downloads it, and Plex streams it to
clients. Homepage discovers all three through their Compose labels.

## Access

Each UI has a dedicated private Tailscale hostname and no published web port:

| Service      | Address                                      |
| ------------ | -------------------------------------------- |
| Scryer       | `https://scryer.<tailnet>.ts.net`            |
| qBittorrent  | `https://qbittorrent.<tailnet>.ts.net`       |
| Plex         | `https://plex.<tailnet>.ts.net/web`          |

The Apple TV must be connected to the tailnet. Funnel is disabled for every
service. qBittorrent's peer port is the only published host port.

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

1. Open qBittorrent, get its temporary password with
   `docker logs qbittorrent`, change it, and set the default save path to
   `/data/downloads`.
2. Open Scryer, create the administrator, and configure `/data/downloads`,
   `/data/movies`, `/data/series`, and `/data/anime`. Add qBittorrent as
   `http://ts-qbittorrent:8080`.
3. Open Plex, claim the server, and add `/data/movies`, `/data/series`, and
   `/data/anime` as libraries.

If qBittorrent rejects its Tailscale hostname, add
`qbittorrent.<tailnet>.ts.net` to **Web UI > Server domains**. Keep its CSRF
and clickjacking protections enabled.

The qBittorrent container sets `QBT_LEGAL_NOTICE=confirm`, as required by the
official image. Use it only for content you are authorized to download and
share.
