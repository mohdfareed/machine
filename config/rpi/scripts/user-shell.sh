#!/bin/bash
# Change user shell to zsh on Linux

echo "Setting up user shell..."

# Install zsh if not already installed
if ! command -v zsh &> /dev/null; then
    echo "Installing zsh..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y zsh
    elif command -v yum &> /dev/null; then
        sudo yum install -y zsh
    else
        echo "❌ Unable to install zsh - unknown package manager"
        exit 1
    fi
fi

# Change default shell to zsh
if [[ "$SHELL" != "$(which zsh)" ]]; then
    echo "Changing default shell to zsh..."
    sudo chsh -s "$(which zsh)" "$USER"
    echo "✓ Default shell changed to zsh"
    echo "Note: You may need to log out and back in for this to take effect"
else
    echo "✓ Default shell is already zsh"
fi
