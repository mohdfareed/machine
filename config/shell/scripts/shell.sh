#!/bin/sh
set -eu

# Install and update the declared Fish plugins.
fish -c 'fisher update'

# Install mc completion.
fish -c 'mc --install-completion'

# Add Fish to /etc/shells if not already present.
fish_path=$(command -v fish)
if ! grep -Fxq "$fish_path" /etc/shells; then
  echo "adding Fish to /etc/shells..."
  printf '%s\n' "$fish_path" | sudo tee -a /etc/shells
fi

# Read the account's login shell; $SHELL can be stale.
user=$(id -un)
if [ "$(uname)" = Darwin ]; then
  current_shell=$(dscl . -read "/Users/$user" UserShell)
  current_shell=${current_shell#*: }
else
  current_shell=$(getent passwd "$user")
  current_shell=${current_shell##*:}
fi

# Set Fish as the default shell.
if [ "$current_shell" != "$fish_path" ]; then
  echo "setting Fish as default shell..."
  chsh -s "$fish_path"
fi
