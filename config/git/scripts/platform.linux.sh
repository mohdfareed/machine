#!/bin/sh
# Git platform config for Linux.

cat > ~/.gitconfig.platform << 'EOF'
[credential]
    helper = cache --timeout=86400
EOF
