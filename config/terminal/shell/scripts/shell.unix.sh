#!/usr/bin/env zsh
set -Eeo pipefail

# Add zsh to /etc/shells if not already present.
zsh_path=$(command -v zsh)
if ! grep -Fxq "$zsh_path" /etc/shells; then
    echo "adding zsh to /etc/shells..."
    printf '%s\n' "$zsh_path" | sudo tee -a /etc/shells
fi

# Read the account's login shell; $SHELL can be stale after a previous deployment.
if [[ "$OSTYPE" == darwin* ]]; then
    current_shell=$(dscl . -read "/Users/$(id -un)" UserShell | awk '{print $2}')
else
    current_shell=$(getent passwd "$(id -un)" | cut -d: -f7)
fi

# Set zsh as the default shell only when the account needs changing.
if [[ "$current_shell" != "$zsh_path" ]]; then
    echo "setting zsh as default shell..."
    chsh -s "$zsh_path"
fi

# Install Zim without replacing the deployed shell files.
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"
if [[ ! -f "$ZIM_HOME/zimfw.zsh" ]]; then
    echo "installing Zim..."
    curl -fsSL --create-dirs -o "$ZIM_HOME/zimfw.zsh" \
        https://github.com/zimfw/zimfw/releases/latest/download/zimfw.zsh
fi

# Install missing modules and build the startup script.
source "$ZIM_HOME/zimfw.zsh" install
