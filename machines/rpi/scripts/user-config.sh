#!/bin/bash

echo "configuring user environment..."

echo "Enabling user lingering for systemd services..."
sudo loginctl enable-linger "$USER"

echo "Ensuring .config directory exists..."
mkdir -p "$HOME/.config"
chmod 755 "$HOME/.config"

echo "user environment configured successfully"
