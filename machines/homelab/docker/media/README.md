# Media

**Plex** serves media to Plex and Infuse, **Scryer** manages acquisition and
subtitles, and **Weaver** downloads Usenet releases.
[Watchlist sync](https://github.com/mohdfareed/plex-watchlist-sync) builds directly
from a pinned Git commit; its code and documentation live in that repository.

## Access

| Service | Private address                     |
| ------- | ----------------------------------- |
| Plex    | `https://plex.<tailnet>.ts.net/web` |
| Scryer  | `https://scryer.<tailnet>.ts.net`   |
| Weaver  | `https://weaver.<tailnet>.ts.net`   |

Scryer has no separate login: anyone permitted to reach it through Tailscale has
administrator access. No ports are published and Funnel is disabled.

## Setup

- Configure Scryer's libraries at `/data/movies`, `/data/series`, and optionally
  `/data/anime`. Keep Plex pointed at the same folders.
- Add your indexer in Scryer using **Newznab → NZBGeek**, and its native Weaver
  integration at `http://ts-weaver:9090` with a Weaver API key.
- Configure Weaver to download to `/data/downloads/incomplete` and move completed
  downloads to `/data/downloads/complete`.
- Set quality profiles and subtitle languages, then configure **OpenSubtitles**.
- Configure Scryer's Plex notifications at `http://ts-plex:32400` to refresh the
  library after imports.
- Follow the standalone tool's [Plex authentication instructions](https://github.com/mohdfareed/plex-watchlist-sync#plex-authentication).
