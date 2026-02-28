FROM homebrew/brew:latest AS brew
FROM ghcr.io/openclaw/openclaw:latest

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
RUN mkdir -p /home/node/.npm && npm install -g openai

# --- Scripts ---
COPY --chmod=755 openclaw.sh /usr/local/bin/openclaw
COPY --chmod=755 entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# --- Entrypoint ---
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gateway"]
