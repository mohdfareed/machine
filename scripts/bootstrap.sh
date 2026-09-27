#!/usr/bin/env sh
set -eu
deploy=false

for arg in "$@"; do case "$arg" in
  "-d"|"--deploy") deploy=true ;;
esac; done

# ═════════════════════════════════════════════════════════════════════════════
# Dependencies
# ═════════════════════════════════════════════════════════════════════════════

case "$(uname -s):$(uname -m):$(uname -r)" in
  Darwin:arm64:*|Linux:*:*[Mm]icrosoft-standard*) ;;
  *) echo "Unsupported host: M1+ macOS or WSL2 required" >&2; exit 1 ;;
esac

# Locate Homebrew before shell configuration has been deployed.
brew="$(command -v brew || true)"
if [ -z "$brew" ]; then
  case "$(uname -s):$(uname -m)" in
    Darwin:arm64) brew=/opt/homebrew/bin/brew ;;
    Linux:*) brew=/home/linuxbrew/.linuxbrew/bin/brew ;;
    *) echo "Unsupported platform: $(uname -s):$(uname -m)" >&2; exit 1 ;;
  esac
fi

# Install Homebrew with its normal terminal prompts, including piped bootstrap.
if ! [ -x "$brew" ]; then
  echo "Installing Homebrew..."
  installer="$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  /bin/bash -c "$installer" </dev/tty
fi

# Activate Homebrew environment for this shell session.
brew_env="$("$brew" shellenv sh)"
eval "$brew_env"

# Install uv and git.
"$brew" install uv
uv="$("$brew" --prefix uv)/bin/uv"
"$brew" install git
git="$(command -v git || true)"

# ═════════════════════════════════════════════════════════════════════════════
# Bootstrap
# ═════════════════════════════════════════════════════════════════════════════

# Resolve machine repo directory.
MC_HOME="${MC_HOME:-$HOME/.machine}"
export MC_HOME

# Clone repo if needed.
if ! [ -d "$MC_HOME/.git" ]; then
  echo "Cloning machine repo to $MC_HOME..."
  "$git" clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Install `mc` with uv, forcing an update if already installed.
"$uv" tool install "$MC_HOME" --editable --force
if [ "$deploy" = true ]; then
  "$uv" run --project "$MC_HOME" mc deploy
fi
