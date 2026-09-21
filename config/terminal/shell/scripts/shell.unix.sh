#!/usr/bin/env zsh
set -Eeo pipefail

# Install declared Zim modules and generate their startup script.
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"
source "$(brew --prefix zimfw)/share/zimfw.zsh" install

# Add zsh to /etc/shells if not already present.
zsh_path=$(command -v zsh)
if ! grep -Fxq "$zsh_path" /etc/shells; then
  echo "adding zsh to /etc/shells..."
  printf '%s\n' "$zsh_path" | sudo tee -a /etc/shells
fi

# Read the account's login shell; $SHELL can be stale.
if [[ "$OSTYPE" == darwin* ]]; then
  current_shell=$(dscl . -read "/Users/$(id -un)" UserShell | awk '{print $2}')
else
  current_shell=$(getent passwd "$(id -un)" | cut -d: -f7)
fi

# Set zsh as the default shell.
if [[ "$current_shell" != "$zsh_path" ]]; then
  echo "setting zsh as default shell..."
  chsh -s "$zsh_path"
fi
