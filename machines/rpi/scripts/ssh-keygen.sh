#!/bin/bash
# Generate SSH key on Linux

KEY_NAME="${1:-id_rsa}"
KEY_PATH="$HOME/.ssh/$KEY_NAME"

echo "Generating SSH key: $KEY_NAME"

# Ensure .ssh directory exists
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Generate SSH key if it doesn't exist
if [[ -f "$KEY_PATH" ]]; then
    echo "SSH key already exists: $KEY_PATH"
else
    echo "Generating new SSH key..."
    ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -N "" -C "$KEY_NAME@$(hostname)"

    # Set proper permissions
    chmod 600 "$KEY_PATH"
    chmod 644 "$KEY_PATH.pub"

    echo "✓ SSH key generated: $KEY_PATH"
fi

echo "Public key content:"
cat "$KEY_PATH.pub"
