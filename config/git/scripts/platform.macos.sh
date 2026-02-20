#!/bin/sh
# Git platform config for macOS.

cat > ~/.gitconfig.platform << 'EOF'
[credential]
    helper = osxkeychain
EOF
