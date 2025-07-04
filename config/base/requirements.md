# Base Machine Requirements

This document defines the explicit requirements that all machines must have for the base configuration to work properly.

## Core Tools (Required)

### Shell & Terminal
- **zsh** - Primary shell (aliased commands expect zsh)
- **git** - Version control and configuration management
- **ssh** - Remote access and key management

### Text Editors
- **nvim** (Neovim) - Default editor configured in gitconfig and aliased as `vim`
- **bat** - Syntax highlighting cat replacement (aliased as `cat`)

### File Management
- **eza** - Modern ls replacement with icons and git integration (aliased as `ls`)

### Development Environment
- **Homebrew** (macOS/Linux) - Package manager for additional tools
- **VSCode** - Integrated development environment (detected via TERM_PROGRAM)

## Base Configuration Files

The following files are provided by the base configuration and assume these tools are available:

- `.gitconfig` - Requires `nvim` as editor and diff/merge tool
- `zshrc` - Requires `zsh`, `bat`, `eza`, `nvim` for aliases
- `zshenv` - Environment setup for all platforms
- `ps_profile.ps1` - PowerShell configuration for Windows
- `vim/` - Neovim configuration directory
- `vscode/` - VSCode settings and snippets

## Installation Notes

### macOS
These tools are typically installed via:
```bash
# Via Homebrew (installed by machine setup)
brew install neovim bat eza git
```

### Linux (Ubuntu/Debian)
```bash
# Core tools
sudo apt install zsh git neovim

# Modern tools (may need additional repos)
sudo apt install bat eza  # or install via cargo/brew
```

### Windows
```bash
# Via Scoop or Winget (handled by machine setup)
scoop install neovim bat eza git
```

## Machine-Specific Extensions

Individual machines may add additional requirements in their own configuration, but must ensure these base requirements are met first.
