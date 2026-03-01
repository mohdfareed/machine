FROM homebrew/brew:latest AS brew
FROM ghcr.io/openclaw/openclaw:latest

# --- OS deps (for native node modules like sqlite3) ---
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    python3 make g++ pkg-config libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*
USER node

# --- Homebrew (Linux) ---
USER root
COPY --from=brew /home/linuxbrew/.linuxbrew /home/linuxbrew/.linuxbrew
RUN chown -R 1000:1000 /home/linuxbrew/.linuxbrew
USER node

# --- Environment ---
ENV PATH="/home/linuxbrew/.linuxbrew/bin:${PATH}"
ENV PATH="/home/linuxbrew/.linuxbrew/sbin:${PATH}"
ENV PATH="/home/node/.npm/bin:${PATH}"
ENV NPM_CONFIG_PREFIX="/home/node/.npm"
ENV NODE_PATH="/home/node/.npm/lib/node_modules"

# --- Modules ---
# LanceDB plugin dependencies
RUN mkdir -p /home/node/.npm && npm install -g openai
RUN cd /app && pnpm add -w @lancedb/lancedb@0.26.2
# sqlite3 native bindings for mem0 plugin
RUN cd /app && pnpm add -w sqlite3

# --- Scripts ---
COPY --chmod=755 openclaw.sh /usr/local/bin/openclaw
COPY --chmod=755 entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# --- Entrypoint ---
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gateway"]
