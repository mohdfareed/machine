#!/bin/bash
# Configure user environment on Linux

echo "Configuring user environment..."

# Enable lingering for systemd user services (for VS Code server, etc.)
echo "Enabling user lingering for systemd services..."
sudo loginctl enable-linger "$USER"

# Create hushlogin to remove login messages
echo "Creating .hushlogin to remove login messages..."
touch "$HOME/.hushlogin"

# Ensure .config directory exists
echo "Ensuring .config directory exists..."
mkdir -p "$HOME/.config"

# Set proper permissions
chmod 755 "$HOME/.config"

echo "✓ User environment configured successfully"
