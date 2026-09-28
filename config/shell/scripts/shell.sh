#!/bin/sh
set -eu

# Add PowerShell to /etc/shells if not already present.
pwsh_path=$(command -v pwsh)
if ! grep -Fxq "$pwsh_path" /etc/shells; then
  echo "adding PowerShell to /etc/shells..."
  printf '%s\n' "$pwsh_path" | sudo tee -a /etc/shells
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

# Set PowerShell as the default shell.
if [ "$current_shell" != "$pwsh_path" ]; then
  echo "setting PowerShell as default shell..."
  chsh -s "$pwsh_path"
fi
