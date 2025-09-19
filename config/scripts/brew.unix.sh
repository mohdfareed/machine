#!/usr/bin/env bash
set -Eeuo pipefail

export NONINTERACTIVE=1

echo "setting up brew..."
if command -v brew &>/dev/null; then
    brew update
    brew cleanup --prune=all
    brew services cleanup

else # install brew
    echo "installing brew..."
    script="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    /bin/bash -c "$(curl -fsSL $script)"
fi
