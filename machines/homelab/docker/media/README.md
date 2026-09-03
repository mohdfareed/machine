<!-- cspell:words Bazarr Prowlarr Radarr SABnzbd Seerr Sonarr VueTorrent -->

# Media

Seerr sends movies to Radarr and series or anime to Sonarr. Prowlarr manages
their indexers, SABnzbd or qBittorrent downloads files, Bazarr adds subtitles,
and Plex serves the library to Plex clients or Infuse.

Normal use is to request something in Seerr and watch it in Plex or Infuse
after it finishes downloading.

## Access

Each UI has a dedicated private Tailscale hostname and no published web port:

| Service               | Address                                      |
| --------------------- | -------------------------------------------- |
| Seerr                 | `https://seerr.<tailnet>.ts.net`             |
| Radarr                | `https://radarr.<tailnet>.ts.net`            |
| Sonarr                | `https://sonarr.<tailnet>.ts.net`            |
| Bazarr                | `https://bazarr.<tailnet>.ts.net`            |
| Prowlarr              | `https://prowlarr.<tailnet>.ts.net`          |
| SABnzbd               | `https://sabnzbd.<tailnet>.ts.net`           |
| Torrents (VueTorrent) | `https://qbittorrent.<tailnet>.ts.net`       |
| Plex                  | `https://plex.<tailnet>.ts.net/web`          |

The dashboard discovers these services through their Compose labels and places
them in the `Media` group. Funnel is disabled. qBittorrent's peer port is the
only published host port.

## Storage

Application state is included in the homelab backup:

```txt
~/.homelab/media/data/{seerr,radarr,sonarr,bazarr,prowlarr,sabnzbd,qbittorrent,plex}
```

Bulk data stays outside `data/` and is not included in that backup:

```txt
downloads/
  torrents/
    incomplete/
  usenet/
    incomplete/
    complete/
movies/
series/
anime/
transcode/
```

`init_media.unix.sh` creates these directories during `mc apply`. Every media
container sees the same tree at `/data`, which allows hard-link imports; Plex
mounts it read-only. Change `HOMELAB_MEDIA_DIR` in
`machines/homelab/machine.env` to move the tree to an external drive.

## First Run

| Service     | Required setup |
| ----------- | -------------- |
| Plex        | Claim the server and add `/data/movies`, `/data/series`, and `/data/anime`. |
| qBittorrent | Use the temporary password from `docker logs qbittorrent`, set a permanent password, use `/data/downloads/torrents` with `/data/downloads/torrents/incomplete`, and select `/vuetorrent` as the alternative WebUI. |
| SABnzbd     | Add the Usenet provider, use `/data/downloads/usenet/incomplete` and `/data/downloads/usenet/complete`, and add `movies` and `series` categories. |
| Radarr      | Add `/data/movies` and configure the download clients. |
| Sonarr      | Add `/data/series` and `/data/anime` and configure the download clients. |
| Prowlarr    | Add the chosen indexers, then connect and fully sync Radarr and Sonarr. |
| Bazarr      | Connect Radarr and Sonarr, then configure subtitle languages and providers. |
| Seerr       | Connect Plex, Radarr, and Sonarr, then select the default roots and quality profiles. |

Use these Docker-network addresses between containers; `localhost` refers to
the container making the request:

| Service     | Internal address              |
| ----------- | ----------------------------- |
| Plex        | `http://ts-plex:32400`         |
| Radarr      | `http://ts-radarr:7878`        |
| Sonarr      | `http://ts-sonarr:8989`        |
| Prowlarr    | `http://ts-prowlarr:9696`      |
| SABnzbd     | `http://ts-sabnzbd:8080`       |
| qBittorrent | `http://ts-qbittorrent:8080`   |

Use the download clients only for content you are authorized to download and
share.
