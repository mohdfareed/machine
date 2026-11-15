#!/bin/sh
set -eu

# Install a quiet login launcher; SSH does not pass shell startup options.
pwsh_path=$(command -v pwsh)
login_shell="$HOME/.local/bin/pwsh-login"
mkdir -p "${login_shell%/*}"
cat > "$login_shell" <<EOF
#!/bin/sh
if [ "\$#" -eq 0 ]; then
    exec "$pwsh_path" -Login -NoLogo
fi
exec "$pwsh_path" -NoLogo "\$@"
EOF
chmod 755 "$login_shell"

# Add PowerShell's login launcher to /etc/shells if not already present.
if ! grep -Fxq "$login_shell" /etc/shells; then
  echo "adding PowerShell to /etc/shells..."
  printf '%s\n' "$login_shell" | sudo tee -a /etc/shells
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
if [ "$current_shell" != "$login_shell" ]; then
  echo "setting PowerShell as default shell..."
  chsh -s "$login_shell"
fi
