#!/usr/bin/env sh
set -eu

# ═════════════════════════════════════════════════════════════════════════════
# Dependencies
# ═════════════════════════════════════════════════════════════════════════════

# Locate Homebrew before shell configuration has been deployed.
brew_command="$(command -v brew || true)"
if [ -z "$brew_command" ]; then
  case "$(uname -s):$(uname -m)" in
    Darwin:arm64) brew_command=/opt/homebrew/bin/brew ;;
    Darwin:*) brew_command=/usr/local/bin/brew ;;
    *) brew_command=/home/linuxbrew/.linuxbrew/bin/brew ;;
  esac
fi

# Install Homebrew with its normal terminal prompts, including piped bootstrap.
if ! [ -x "$brew_command" ]; then
  echo "Installing Homebrew..."
  installer="$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  /bin/bash -c "$installer" </dev/tty
fi

# Keep uv owned and updated by Homebrew, independent of selected modules.
brew_env="$("$brew_command" shellenv sh)"
eval "$brew_env"
"$brew_command" install uv
uv_command="$("$brew_command" --prefix uv)/bin/uv"

# ═════════════════════════════════════════════════════════════════════════════
# Bootstrap
# ═════════════════════════════════════════════════════════════════════════════

# Resolve machine repo directory.
MC_HOME="$(eval echo "${MC_HOME:-$HOME/.machine}")"
export MC_HOME

# Clone repo if needed.
if ! [ -d "$MC_HOME/.git" ]; then
  echo "Cloning machine repo to $MC_HOME..."
  git clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Sync and deploy the repo.
"$uv_command" run --project "$MC_HOME" mc sync
"$uv_command" run --project "$MC_HOME" mc deploy
