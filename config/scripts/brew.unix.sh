#!/usr/bin/env bash

echo "setting up brew..."

if command -v brew &>/dev/null; then
    brew update
    brew cleanup --prune=all
    brew services cleanup
else # install brew
    script="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    /bin/bash -c "$(curl -fsSL $script)"
fi

echo "brew set up successfully"
