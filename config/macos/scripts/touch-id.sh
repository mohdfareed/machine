#!/bin/bash
# Enable Touch ID for sudo on macOS

echo "Enabling Touch ID for sudo..."

PAM_SUDO_PATH="/etc/pam.d/sudo_local"
PAM_SUDO_CONTENT="auth       sufficient     pam_tid.so"

# Create the sudo_local file if it doesn't exist
if [[ ! -f "$PAM_SUDO_PATH" ]]; then
    echo "Creating $PAM_SUDO_PATH..."
    sudo mkdir -p "$(dirname "$PAM_SUDO_PATH")"
    sudo touch "$PAM_SUDO_PATH"
fi

# Check if Touch ID is already enabled
if grep -q "pam_tid.so" "$PAM_SUDO_PATH"; then
    echo "Touch ID for sudo is already enabled"
    exit 0
fi

# Add Touch ID authentication
echo "Adding Touch ID authentication to sudo..."
echo "$PAM_SUDO_CONTENT" | sudo tee "$PAM_SUDO_PATH" > /dev/null

echo "✓ Touch ID for sudo enabled successfully"
echo "You can now use Touch ID to authenticate sudo commands"
