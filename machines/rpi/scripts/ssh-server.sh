#!/bin/bash
# Set up SSH server on Linux

echo "Setting up SSH server on Linux..."

# Install OpenSSH server if not already installed
if ! command -v sshd &> /dev/null; then
    echo "Installing OpenSSH server..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y openssh-server
    elif command -v yum &> /dev/null; then
        sudo yum install -y openssh-server
    else
        echo "❌ Unable to install SSH server - unknown package manager"
        exit 1
    fi
fi

# Enable and start SSH service
sudo systemctl enable ssh
sudo systemctl start ssh

# Configure SSH to start on boot
sudo systemctl enable ssh.service

echo "✓ SSH server setup completed"
echo "SSH is now enabled and will start on boot"
echo "You can connect using: ssh $(whoami)@$(hostname -I | awk '{print $1}')"
