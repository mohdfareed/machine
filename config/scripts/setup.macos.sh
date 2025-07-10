#!/usr/bin/env zsh

echo "updating macos tools..."

if command -v brew &>/dev/null; then
    brew update && brew upgrade
    brew cleanup --prune=all
else # install brew
    script="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    /bin/bash -c "$(curl -fsSL $script)"
fi

if command -v mas &>/dev/null; then
    mas upgrade
fi

echo "macos tools updated successfully"
