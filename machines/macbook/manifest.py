"""Macbook machine manifest."""

from machine.dotfiles import ghostty, git, nvim, vscode
from machine.manifest import Dotfile, MachineManifest, brew, cask, mas

manifest = MachineManifest(
    dotfiles=[
        # Shared configs
        *git(),
        *nvim(),
        *vscode(),
        *ghostty(),
        # Machine shell configs
        Dotfile(source="machines/macbook/zshenv", target="~/.zshenv"),
        Dotfile(source="machines/macbook/zshrc", target="~/.zshrc"),
        # Machine SSH
        Dotfile(source="machines/macbook/ssh.config", target="~/.ssh/config"),
    ],
    packages=[
        # Git
        *brew("git", "git-lfs", "gh"),
        # Shell
        *brew("zsh", "fzf", "bat", "eza", "btop", "oh-my-posh"),
        # Dev tools
        *brew("neovim", "lazygit", "ripgrep", "fd"),
        # Python
        *brew("python", "python-freethreading", "uv"),
        # PowerShell
        *cask("powershell"),
        # Fonts
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
        # System
        *brew("fastfetch", "copilot-cli"),
        # Dev languages
        *brew("go", "shellcheck"),
        *cask("dotnet-sdk", "visual-studio-code", "docker"),
        # Utilities
        *brew("mas", "gnu-time"),
        # Apps
        *cask("tailscale", "ghostty", "chatgpt"),
        *cask("iina", "mos", "monitorcontrol", "swish", "figma", "sf-symbols"),
        # Mac App Store
        *mas(Xcode=497799835, Craft=1487937127, Copilot=1447330651),
        *mas(Keynote=409183694, Numbers=409203825, Pages=409201541),
        *mas(Noir=1592917505, AdGuard=1440147259, Peek=1554235898),
    ],
)
