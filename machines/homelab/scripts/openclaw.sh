#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy OpenClaw config with env var substitution.
#
# The repo stores config files with ${VAR} placeholders (secrets, tailnet
# name, etc.). The OpenClaw CLI resolves these at runtime, but the macOS
# GUI app reads them as-is — it has no shell env to substitute from.
#
# We can't symlink ~/.openclaw → repo and template in place because that
# would write resolved secrets into the git-tracked source files.
#
# Instead, this script copies config files into a real ~/.openclaw/,
# resolving ${VAR} references from the environment. Directories that
# don't contain secrets (cron, workspace) are symlinked back to the repo.

SRC="$MC_HOME/machines/$MC_ID/openclaw"
DST="$HOME/.openclaw"

# If ~/.openclaw is a directory symlink from a previous deploy, remove it.
# Runtime data lived in the repo dir (gitignored) — OpenClaw recreates it.
[[ -L "$DST" ]] && rm "$DST"

mkdir -p "$DST/config"

# Resolve ${VAR} references with values from environment.
template() {
    perl -pe 's/\$\{(\w+)\}/defined $ENV{$1} ? $ENV{$1} : "\${$1}"/ge' "$1" > "$2"
    chmod 600 "$2" # may contain secrets
}

# Template main config and all included configs.
template "$SRC/openclaw.json" "$DST/openclaw.json"
for f in "$SRC"/config/*.json5; do
    [[ -f "$f" ]] || continue
    template "$f" "$DST/config/$(basename "$f")"
done

# Symlink directories that don't need templating.
for dir in cron workspace; do
    [[ -d "$SRC/$dir" ]] || continue
    target="$DST/$dir"
    if [[ -L "$target" ]]; then
        [[ "$(readlink "$target")" == "$SRC/$dir" ]] && continue
        rm "$target"
    fi
    [[ -e "$target" ]] || ln -s "$SRC/$dir" "$target"
done

echo "openclaw: config deployed → $DST"
