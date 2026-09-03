<!-- cspell:words Bazarr Jimaku Newznab NewsDemon NZBGeek Prowlarr Radarr SABnzbd Seerr Sonarr Torznab Usenet -->

# Media

Seerr is the everyday discovery and request interface. It sends movies to
Radarr and series or anime to Sonarr. Those applications search the indexers
managed by Prowlarr, download through SABnzbd or qBittorrent, and import the
finished files. Bazarr fills in missing subtitles, while Plex serves the
library to Plex clients or Infuse.

This is a download-first library workflow, not torrent playback while a file
is still downloading. In normal use, request something in Seerr (or add it to
the Plex Watchlist), wait for it to become available, and watch it in Plex or
Infuse. The other interfaces are for initial setup and troubleshooting.

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

Homepage discovers all of them through the Compose labels and keeps them in
the existing `Services` group. Funnel is disabled. qBittorrent's peer port is
the only published host port.

## Storage

Application state follows the normal service convention and is included in the
homelab backup:

```txt
~/.homelab/media/data/{seerr,radarr,sonarr,bazarr,prowlarr,sabnzbd,qbittorrent,plex}
```

Bulk data stays outside `data/` so it is not copied into the daily iCloud
backup. `HOMELAB_MEDIA_DIR` currently expands to
`~/.homelab/storage/media`:

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

The `init_media.unix.sh` script creates these directories automatically during
`mc apply`; no manual `mkdir` step is required. Every importer and downloader
sees the same parent as `/data`, so no remote path mappings are needed and
torrent imports can use hard links instead of duplicating files. Plex mounts
the same parent read-only.

Change only `HOMELAB_MEDIA_DIR` in `machines/homelab/machine.env` when moving
bulk data to an external drive.

## External Accounts

The paid Usenet route needs two external services:

| Service   | What it supplies                         | Credential used here       |
| --------- | ---------------------------------------- | -------------------------- |
| NewsDemon | Access to Usenet article data            | NNTP username and password |
| NZBGeek   | Searchable NZB index and release metadata | API key                    |

SABnzbd, Prowlarr, Radarr, Sonarr, Bazarr, and Seerr are self-hosted and do
not require paid accounts. An OpenSubtitles.com account is useful for general
subtitles. A Jimaku API key is optional and only useful when Japanese-language
subtitles are wanted.

Start with one provider and one indexer. If completion failures become common,
add a second NZB indexer and a block account from a Usenet provider on a
different backbone; neither is needed for the initial setup.

## First Run

Complete setup in this order so every API key exists before another service
needs it.

1. In Plex, claim the server and add `/data/movies`, `/data/series`, and
   `/data/anime` as libraries. Enable automatic library scanning.
2. In SABnzbd, add NewsDemon at `news.newsdemon.com`, port `563`, with SSL and
   certificate verification enabled. Enter the NewsDemon NNTP credentials and
   test the server. Use `/data/downloads/usenet/incomplete` and
   `/data/downloads/usenet/complete` for the temporary and completed folders,
   then add `movies` and `series` categories. Copy SABnzbd's full API key from
   **Config > General**.
3. In Radarr, add `/data/movies`; in Sonarr, add `/data/series` and
   `/data/anime`. Choose the quality profiles and size limits that should be
   offered in Seerr. Copy both API keys from **Settings > General > Security**.
4. Add SABnzbd and qBittorrent as download clients in both Radarr and Sonarr,
   using the internal addresses below. Use category `movies` in Radarr and
   `series` in Sonarr. To prefer Usenet while retaining torrents as fallback,
   create a delay profile with no Usenet delay and a torrent delay such as 60
   minutes.
5. In Prowlarr, add NZBGeek and its API key. Add only torrent indexers or
   trackers that you are authorized to use. Under **Settings > Apps**, add
   Radarr and Sonarr, use `http://ts-prowlarr:9696` as the Prowlarr server URL,
   and enable full sync. Prowlarr is then the only place indexers need to be
   maintained.
6. In Bazarr, connect Radarr and Sonarr, create the desired language profiles,
   and enable multiple subtitle providers. Start with OpenSubtitles.com for
   general content; add Jimaku only for Japanese subtitles. Store subtitles
   alongside the media files.
7. In Seerr, sign in with the Plex account, connect Plex, Radarr, and Sonarr,
   and select the default quality profiles and root folders. Sonarr can use
   `/data/series` for regular shows and `/data/anime` as its anime directory.
   Enable library scans and automatic search. For one-step daily use, grant
   auto-request and auto-approve permissions and enable Plex Watchlist auto
   requests in the Seerr user profile.

Use these Docker-network addresses; `localhost` would refer to the wrong
container:

| Configure in    | Target      | Internal address              | Credential       |
| --------------- | ----------- | ----------------------------- | ---------------- |
| Seerr           | Plex        | `http://ts-plex:32400`         | Plex sign-in     |
| Seerr           | Radarr      | `http://ts-radarr:7878`        | Radarr API key   |
| Seerr           | Sonarr      | `http://ts-sonarr:8989`        | Sonarr API key   |
| Prowlarr        | Radarr      | `http://ts-radarr:7878`        | Radarr API key   |
| Prowlarr        | Sonarr      | `http://ts-sonarr:8989`        | Sonarr API key   |
| Radarr/Sonarr   | SABnzbd     | `http://ts-sabnzbd:8080`       | SABnzbd API key  |
| Radarr/Sonarr   | qBittorrent | `http://ts-qbittorrent:8080`   | None             |
| Bazarr          | Radarr      | `http://ts-radarr:7878`        | Radarr API key   |
| Bazarr          | Sonarr      | `http://ts-sonarr:8989`        | Sonarr API key   |

qBittorrent bypasses authentication only for loopback and private container
subnets; host-header, CSRF, and clickjacking protections remain enabled. Its
browser UI and internal Web API therefore need no credentials in this private
deployment. Do not publish its web port without removing that bypass and
enabling credentials.

Seerr and Plex still require Plex authentication. The Arr applications require
an authentication method on first run; selecting **Disabled for Local
Addresses** avoids repeated prompts for local proxy traffic while preserving
their API-key authentication.

Use NewsDemon over TLS. A VPN is not required for the encrypted Usenet
connection. Torrent traffic still uses the server's normal internet connection
unless a VPN is configured separately. Use either source only for content you
are authorized to download and share.

## Scryer Migration

The next deployment's existing `--remove-orphans` behavior stops and removes
the old Scryer container. It does not delete `data/scryer`, the old Tailscale
state volume, or the old Tailscale device, so the data remains available until
the replacement has been verified and cleanup is explicitly requested.
