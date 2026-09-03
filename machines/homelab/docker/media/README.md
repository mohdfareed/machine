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
  torrents/ # completed torrents
    incomplete/
  usenet/
    incomplete/
    complete/
movies/
series/
anime/
```

Every media container sees the same tree at `/data`, which allows hard-link imports;
Plex mounts it read-only. On macOS, the script also exposes the tree as the
authenticated, read-only SMB share `Media`. Change `HOMELAB_MEDIA_DIR` in
`machines/homelab/machine.env` to move the tree to an external drive.

## First Run

Configure the services in this order. When one container asks for another
service, use these internal addresses; `localhost` refers to the container
making the request:

| Service     | Internal address              |
| ----------- | ----------------------------- |
| Plex        | `http://ts-plex:32400`         |
| Radarr      | `http://ts-radarr:7878`        |
| Sonarr      | `http://ts-sonarr:8989`        |
| Prowlarr    | `http://ts-prowlarr:9696`      |
| SABnzbd     | `http://ts-sabnzbd:8080`       |
| qBittorrent | `http://ts-qbittorrent:8080`   |

1. **Set up Plex.** Claim the server and add libraries for `/data/movies`,
   `/data/series`, and `/data/anime`.

2. **Set up the download clients you intend to use.** For qBittorrent, use the
   temporary password from `docker logs qbittorrent`, set a permanent password,
   set `/data/downloads/torrents` as the save path and
   `/data/downloads/torrents/incomplete` as the incomplete path, then select
   `/vuetorrent` as the alternative WebUI. For SABnzbd, add the Usenet provider,
   set the incomplete and complete folders under `/data/downloads/usenet`, and
   add `movies` and `series` categories.

3. **Set up Radarr and Sonarr.** Add `/data/movies` as Radarr's root. Add
   `/data/series` and `/data/anime` as Sonarr roots. Connect each app to the
   download clients above, using category `movies` in Radarr and `series` in
   Sonarr.

4. **Set up Prowlarr.** Add the chosen indexers, then add Radarr and Sonarr
   under **Settings > Apps** with full synchronization.

5. **Set up Bazarr.** Enable its Sonarr and Radarr integrations using the
   internal addresses above and the API key from each app. Leave path mappings
   empty because all three containers see the same `/data` paths. Create an
   English and Arabic language profile, make it the default for series and
   movies, add the subtitle providers, and store subtitles alongside the media.

6. **Set up Seerr last.** Connect Plex, Radarr, and Sonarr using their internal
   addresses and API keys, then select the default roots and quality profiles.

After initial setup, normal use is Seerr for requests and Plex or Infuse for
watching. Open the other services only for administration or troubleshooting.

> Use the download clients only for content you are authorized to download and share.
