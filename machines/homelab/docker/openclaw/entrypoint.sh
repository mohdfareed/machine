#!/bin/bash
set -e

BREW_HOME="/home/linuxbrew/.linuxbrew"
NPM_PREFIX="/home/node/.npm"

# --- Environment (always set — gateway and CLI) ---
if [ -x "$BREW_HOME/bin/brew" ]; then
    eval "$("$BREW_HOME/bin/brew" shellenv)"
fi

export NPM_CONFIG_PREFIX="$NPM_PREFIX"
export PATH="$NPM_PREFIX/bin:$PATH"
export NODE_PATH="$NPM_PREFIX/lib/node_modules:${NODE_PATH:-}"

# --- Gateway first-run setup (skipped for CLI invocations) ---
if [ "$1" = "gateway" ]; then
    # Linuxbrew (persisted via volume)
    if [ ! -x "$BREW_HOME/bin/brew" ]; then
        echo "[entrypoint] Installing Homebrew..."
        git clone --depth=1 https://github.com/Homebrew/brew "$BREW_HOME/Homebrew"

        mkdir -p "$BREW_HOME/bin"
        ln -sf ../Homebrew/bin/brew "$BREW_HOME/bin/brew"
        eval "$("$BREW_HOME/bin/brew" shellenv)"
        echo "[entrypoint] Homebrew installed."
    fi

    # npm modules (persisted via volume — global install so they survive recreates)
    mkdir -p "$NPM_PREFIX"
    if ! npm list -g openai >/dev/null 2>&1; then
        echo "[entrypoint] Installing npm modules..."
        npm install -g openai
        echo "[entrypoint] Done."
    fi

    # Tighten session file permissions
    find /home/node/.openclaw -name "sessions.json" -exec chmod 600 {} + 2>/dev/null || true
fi

exec node /app/dist/index.js "$@"
