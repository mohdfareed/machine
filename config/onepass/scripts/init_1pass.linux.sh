#!/usr/bin/env bash
set -Eeuo pipefail

# Source: https://support.1password.com/install-linux/#debian-or-ubuntu
# CLI architectures: https://www.1password.dev/cli/get-started

# Install the tools needed to register the repository before ordinary packages.
if ! command -v curl >/dev/null || ! command -v gpg >/dev/null; then
  sudo apt update
  sudo apt install -y ca-certificates curl gnupg
fi

# Add the key for the 1Password apt repository.
curl -fsS https://downloads.1password.com/linux/keys/1password.asc | \
  sudo gpg --dearmor --yes --output /usr/share/keyrings/1password-archive-keyring.gpg

# Add the 1Password apt repository for this system's architecture.
architecture=$(dpkg --print-architecture)
echo "deb [arch=$architecture signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$architecture stable main" | \
  sudo tee /etc/apt/sources.list.d/1password.list

# Add the debsig-verify policy.
sudo mkdir -p /etc/debsig/policies/AC2D62742012EA22/
curl -fsS https://downloads.1password.com/linux/debian/debsig/1password.pol | \
  sudo tee /etc/debsig/policies/AC2D62742012EA22/1password.pol
sudo mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22
curl -fsS https://downloads.1password.com/linux/keys/1password.asc | \
  sudo gpg --dearmor --yes --output /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg

# Refresh package metadata; module.py declares the 1Password packages to install.
sudo apt update
