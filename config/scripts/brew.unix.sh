#!/usr/bin/env bash

echo "setting up brew..."

if command -v brew &>/dev/null; then
    brew cleanup --prune=all
else # install brew
    script="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    /bin/bash -c "$(curl -fsSL $script)"
fi

echo "brew set up successfully"
