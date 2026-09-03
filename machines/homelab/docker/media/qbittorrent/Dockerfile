ARG VUETORRENT_VERSION=2.35.0
ARG VUETORRENT_SHA256=6e0c0e6acb563710aaf32cd165cf34da0e5d61bc1a68386e4cf97a648fa8171c

FROM alpine:3.22 AS vuetorrent
ARG VUETORRENT_VERSION
ARG VUETORRENT_SHA256

RUN apk add --no-cache curl unzip \
    && curl -fsSL \
        "https://github.com/VueTorrent/VueTorrent/releases/download/v${VUETORRENT_VERSION}/vuetorrent.zip" \
        -o /tmp/vuetorrent.zip \
    && echo "${VUETORRENT_SHA256}  /tmp/vuetorrent.zip" | sha256sum -c - \
    && unzip -q /tmp/vuetorrent.zip -d /tmp \
    && test -f /tmp/vuetorrent/public/index.html \
    && chmod -R a=rX /tmp/vuetorrent

FROM qbittorrentofficial/qbittorrent-nox:latest

COPY --from=vuetorrent /tmp/vuetorrent /vuetorrent
