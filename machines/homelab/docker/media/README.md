<!-- cspell:words Bazarr Prowlarr Radarr Seerr Sonarr Weaver -->

# Media

Seerr sends movies to Radarr and series to Sonarr. Prowlarr manages their
indexers, Weaver downloads and post-processes Usenet releases, Bazarr adds
subtitles, and Plex serves the library to Plex clients or Infuse. Arr Dashboard
provides a unified administration interface for the stack.

Normal use is to request something in Seerr and watch it in Plex or Infuse after
it finishes downloading.

## Access

Each UI has a dedicated private Tailscale hostname and no published web port:

| Service       | Address                                  |
| ------------- | ---------------------------------------- |
| Plex          | `https://plex.<tailnet>.ts.net/web`      |
| Seerr         | `https://seerr.<tailnet>.ts.net`         |
| Weaver        | `https://weaver.<tailnet>.ts.net`        |
| Arr Dashboard | `https://arr-dashboard.<tailnet>.ts.net` |
| Radarr        | `https://radarr.<tailnet>.ts.net`        |
| Sonarr        | `https://sonarr.<tailnet>.ts.net`        |
| Bazarr        | `https://bazarr.<tailnet>.ts.net`        |
| Prowlarr      | `https://prowlarr.<tailnet>.ts.net`      |

The dashboard discovers these services through their Compose labels. Plex,
Seerr, Weaver, and Arr Dashboard appear in `Media`; supporting services appear
in `Media Infrastructure`. Funnel is disabled.

## Storage

Application state is included in the homelab backup:

```txt
~/.homelab/media/data/{plex,seerr,weaver,arr-dashboard,radarr,sonarr,bazarr,prowlarr}
```

Bulk data stays outside `data/` and is not included in that backup:

```txt
downloads/
   incomplete/
   complete/
      movies/
      tv/
movies/
series/
```

Weaver, Radarr, Sonarr, and Bazarr see the same tree at `/data`, so completed
files do not need remote path mappings. Plex also mounts the tree at `/data` and
has write access so media deletion from Plex works. On macOS, the initialization
script exposes the tree separately as the authenticated, read-only SMB share
`Media`.

Change `MC_HOMELAB_MEDIA_DIR` in `machines/homelab/machine.env` to move the tree
to an external drive. The initialization script refuses to create a replacement
directory under `/Volumes` when the configured external volume is absent.

## First Run

When one container asks for another service, use these internal addresses;
`localhost` refers to the container making the request:

| Service  | Internal address          |
| -------- | ------------------------- |
| Plex     | `http://ts-plex:32400`    |
| Weaver   | `http://ts-weaver:9090`   |
| Radarr   | `http://ts-radarr:7878`   |
| Sonarr   | `http://ts-sonarr:8989`   |
| Prowlarr | `http://ts-prowlarr:9696` |

Configure the services in this order:

1. **Plex:** claim the server and add libraries rooted at `/data/movies` and
   `/data/series`. Enable **Settings > Library > Allow media deletion** if Plex
   should be able to delete source files. The `/data` mount is writable.

2. **Weaver:** add the Usenet provider and use `/data/downloads/incomplete` and
   `/data/downloads/complete` as its intermediate and complete directories.
   Create `movies` and `tv` categories. Create a separate Integration-scoped API
   key for each automation client.

3. **Radarr and Sonarr:** use `/data/movies` as Radarr's root and `/data/series`
   as Sonarr's root. Add Weaver as an **NZBGet** client with host `ts-weaver`,
   port `9090`, SSL disabled, any non-empty username, and the Weaver API key in
   the password field. Use category `movies` for Radarr and `tv` for Sonarr.
   Leave remote path mappings empty because both sides use `/data`.

4. **Prowlarr:** add the chosen indexers, then add Radarr and Sonarr under
   **Settings > Apps** with full synchronization.

5. **Bazarr:** connect Sonarr and Radarr with their internal addresses and API
   keys. Leave path mappings empty. Create the desired language profiles, add
   subtitle providers, and store subtitles beside the media. Use
   `http://127.0.0.1:9000` for the Whisper endpoint.

6. **Seerr:** connect Plex, Radarr, and Sonarr with their internal addresses and
   API keys, then select the default roots and quality profiles.

7. **Arr Dashboard:** set its External URL to its private HTTPS address, add the
   internal service addresses, and let the initial caches synchronize. Keep
   cleanup, queue cleaner, hunting, auto-tagging, and automated TRaSH deployment
   disabled until their previews and effects have been reviewed.

Removing a container does not remove its bind-mounted directory under `data/`.
Never use `docker compose down -v` for this stack unless deleting persistent
state is explicitly intended.

> Use the download client only for content you are authorized to download and share.
