# Machine Setup Project Review

## Project Status: MIGRATION TO CHEZMOI PLANNED

**DECISION**: Full migration to Chezmoi - no Python needed!

**Research findings from https://chezmoi.io:**
- ✅ **Scripts handle everything**: `run_once_`, `run_onchange_`, template scripts 
- ✅ **Package management**: Cross-platform templated scripts
- ✅ **Machine detection**: Built-in `.chezmoi.os`, `.chezmoi.hostname`, custom config
- ✅ **Secrets**: Multiple password managers + encryption built-in
- ✅ **One-command bootstrap**: `chezmoi init --apply repo`
- ✅ **Standard locations**: No path configuration needed

**What Chezmoi scripts can replace:**
- Package installation (brew/winget/apt) via `run_onchange_install-packages.sh.tmpl`
- System setup (SSH keys, preferences) via `run_once_setup-system.sh`
- Tool configuration via templated files and scripts
- Private file handling via password manager integration or encryption

**Python eliminated** - Chezmoi's Go binary + shell scripts handle everything.

**HOW PROFESSIONAL TOOLS SOLVE THIS (Research Results)**:

**Top Modern Options (2024-2025):**
1. **Chezmoi** (15k+ stars) - Still the dominant choice
   - Go-based, cross-platform, mature ecosystem
   - Built-in templating, secrets management, machine detection
   - Work/home profiles, 1Password integration
   
2. **Nix Home Manager** - Growing rapidly
   - Declarative configuration, package management included
   - Reproducible environments, version locking
   - Learning curve but very powerful
   
3. **Rust alternatives** (newer, smaller communities):
   - **Dotter** (1k stars) - Windows/Linux/Mac support
   - **Comtrya** (556 stars) - Configuration management
   - **Rotz** - Cross-platform, but limited adoption

**Key Insight**: Chezmoi is still the clear winner in 2024/2025. The Rust alternatives haven't gained significant traction, and Nix Home Manager is powerful but has a steeper learning curve.

**Recommendation**: Try Chezmoi first - it directly solves your templating, cross-platform, and secrets problems. If it covers 80% of your needs, use it and build custom scripts for the remaining 20%.

## CHEZMOI WORKFLOW ANALYSIS

Based on research, here's how your workflows would look with Chezmoi:

### 📦 **Bootstrap New Machine**
```bash
# Single command setup (replaces your entire deploy script)
chezmoi init --apply https://github.com/yourusername/dotfiles.git

# With private repo
chezmoi init --apply git@github.com:yourusername/dotfiles.git

# What it does:
# 1. Clones to ~/.local/share/chezmoi/ (standardized location)
# 2. Detects machine type automatically (via chezmoi.toml config)
# 3. Applies all dotfiles with templates processed
# 4. Handles secrets via password manager integration
```

### 🔧 **Add/Track New Tool**
```bash
# Add a new config file to tracking
chezmoi add ~/.zshrc
chezmoi add ~/.config/nvim/init.lua

# Add with templating (for machine-specific differences)
chezmoi add --template ~/.gitconfig
chezmoi add --template ~/.ssh/config

# Commit changes
chezmoi cd  # Go to source directory
git add . && git commit -m "Add new tool config"
git push
```

### ⚙️ **Configure Machine-Specific Things**
```bash
# Templates use built-in variables:
{{ .chezmoi.os }}          # "darwin", "linux", "windows"  
{{ .chezmoi.arch }}        # "amd64", "arm64"
{{ .chezmoi.hostname }}    # "MacBook-Pro", "rpi4"

# Example .zshrc template:
{{- if eq .chezmoi.os "darwin" }}
export ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
export DEV="$HOME/Developer"
{{- else if eq .chezmoi.os "linux" }}
export DEV="$HOME/projects"  
{{- end }}

# Custom variables in ~/.config/chezmoi/chezmoi.toml:
[data]
    machine_type = "laptop"
    work = true
```

### 🔄 **Sync Changes**
```bash
# Pull latest changes from repo and apply
chezmoi update

# See what would change before applying
chezmoi diff

# Push local changes
chezmoi cd
git add . && git commit -m "Update configs"
git push
```

### 🔐 **Handle Private Files**
```bash
# Method 1: Templates with password manager
chezmoi add --template ~/.ssh/id_rsa

# In template, reference 1Password:
{{ (onepassword "SSH Key" "Personal").privateKey }}

# Method 2: External private files (like your current system)
# Keep private files separate, reference in templates:
{{ .chezmoi.sourceDir }}/../private/ssh_keys/id_rsa

# Method 3: Age encryption (built-in)
chezmoi add --encrypt ~/.ssh/id_rsa
```

### 🎯 **Key Advantages Over Your Current System**
1. **No template variables** - Built-in machine detection
2. **Standard locations** - `~/.local/share/chezmoi/` (no path confusion)
3. **One command bootstrap** - Replaces your deploy script
4. **Built-in secrets** - Password manager integration
5. **Automatic updates** - `chezmoi update` pulls and applies

### 🔧 **What You'd Still Need Python For**
- Package installation (brew bundle, etc.)
- System preferences (macOS defaults)
- SSH key generation
- Service setup (Docker, etc.)

But these could be simple `run_once_` scripts in Chezmoi.

**WHAT YOU ACTUALLY NEED**: 
- Pick a standard location pattern like the pros
- Stop fighting the fundamental complexity - embrace it with a cleaner pattern

## Current Implementation Status

### ✅ Completed Features
- **New CLI Architecture**: Simple command structure (`setup`, `update`, tool commands)
- **Machine Detection**: Via $MACHINE env var with CLI fallback
- **Package Management**: Direct brewfile/apt.pkg parsing and installation
- **Config File Linking**: Improved mapping with base/machine structure
- **Private Files**: SSH keys and environment variable handling
- **Dry-run Mode**: Safe testing with `--dry-run` flag
- **Rich Logging**: File logs with session separators and improved formatting
- **Shell Execution**: Real-time output with loading indicators
- **Tool Auto-discovery**: Automatic detection of available tools/configs
- **Test Suite**: Comprehensive tests with dry-run and test machine validation
- **Platform Scripts**: Cleaned up macOS/Linux shell scripts

### 🔧 Critical Issues Identified
1. **Test Quality**: Current tests are minimal and lack proper assertions/coverage
2. **Config Structure Clarity**: Need to verify template vs direct linking approach is consistent
3. **Missing Base Requirements**: Need explicit dependencies (vscode, nvim, zsh, etc.)
4. **Documentation**: README needs complete rewrite
5. **Project Config**: Review .github/, .vscode/, pyproject.toml

### 📝 Immediate Action Items
1. **Deployment Strategy**: Implement uv-based installation with cross-platform support
2. **Environment Variable Strategy**: Implement system-wide environment variables (not just shell-specific)
3. **Multi-Shell Support**: Detect and configure all available shells, not just zsh/pwsh
4. **XDG Compliance**: Use proper system directories with user override options
5. **Fix Test Suite**: Rewrite tests with proper assertions and coverage
6. **Update Documentation**: Comprehensive README rewrite

## New Architecture Overview
```
config/
├── base/              # Foundation configs (was "shared")
│   ├── zshrc, zshenv, gitconfig, vscode-settings.json
├── macbook-personal/  # Machine-specific overrides
├── macbook-work/
└── gaming-pc/
```

### Systems:
1. **Shell**: CLI generates `~/.zshenv` template that defines machine + sources base + machine configs
2. **Config Files**: Direct symlinks to base files, with conditional loading for machine-specific additions
3. **Packages**: TBD - need to design package management approach
4. **CLI Commands**: TBD - need to design command structure

This eliminates complex chains and file generation.

## Current Codebase Waste
- ~80% is architectural boilerplate (Plugin[C,E], protocols, abstractions)
- ~20% is actual useful functionality that should be preserved

## Better Approaches Observed
Popular dotfiles repos use simple patterns:
- **Homebrew's Brewfile** (industry standard)
- **GNU Stow** for dotfile linking
- **Simple shell scripts** with modular functions
- **Makefiles** for task organization
- **Ansible** for complex multi-machine setups (overkill here)

# Complete Feature Inventory

## PYTHON ARCHITECTURE ANALYSIS:

### Machine Classes (5 machines):
- **MacOS**: 12 plugins, Brewfile + system preferences + Touch ID setup
- **Windows**: 10 plugins, Winget + Scoop, PowerShell execution policy
- **RPi**: 12 plugins, Snap packages, SSH server setup, user shell change
- **Gleason** (work Windows): 10 plugins, specialized for work environment
- **Codespaces**: 3 plugins, minimal GitHub Codespaces setup

### Plugin System (12+ plugins):
- **ZSH**: Installs zsh/tmux/bat/eza, creates machine env vars, updates Zinit
- **PowerShell**: Cross-platform PowerShell installation + profile setup
- **Git**: Links gitconfig/gitignore, installs git/git-lfs/gh
- **SSH**: Key generation, server setup, keychain integration
- **VSCode**: Settings linking, tunnel setup for remote access
- **NeoVim**: LazyVim setup and configuration
- **Private**: SSH keys and environment variables from external directory
- **Tools**: Fonts, Docker, Python, Node, Tailscale, Btop installations

### Package Managers (6 different systems):
- **Brew** (macOS/Linux)
- **Winget** (Windows)
- **Scoop** (Windows)
- **APT** (Linux)
- **Snap** (Linux)
- **MAS** (Mac App Store)

## EXHAUSTIVE LIST OF EVERYTHING CURRENTLY BEING CONFIGURED:

### Shell Environment (Zsh):
- **Zinit plugin manager** with 6+ plugins
- **Oh-my-posh theme** (Pure theme)
- **FZF fuzzy finder** with custom key bindings
- **Fast syntax highlighting**
- **Zsh autosuggestions**
- **Zsh completions** with case-insensitive matching
- **Custom history settings** (ignore dups, shared history, etc.)
- **XDG Base Directory Specification** compliance (14 environment variables!)
- **Homebrew integration** across 3 different platforms
- **Pyenv integration** (Python version manager)
- **Dotnet completions** (custom function)
- **NVM integration** (Node version manager)

### Development Environment:
- **Python**: pyenv, pipx, virtual environments, PYTHONPYCACHEPREFIX, PYTHONUSERBASE, IPYTHONDIR, JUPYTER_PLATFORM_DIRS
- **Node.js**: NVM_DIR, custom paths
- **Go**: GOPATH, custom bin paths
- **Docker**: DOCKER_CONFIG path
- **Git**: SSH signing, nvim as editor, custom config
- **.NET**: DOTNET_ROOT for macOS/Linux, custom tools path

### Editor Configurations:
- **Neovim**: LazyVim distribution, lazy.nvim plugin manager, custom plugins, OneDark theme
- **VSCode**: 223-line settings file with extensive customization, GitHub Copilot integration, comment anchors, markdown settings, JSON formatting
- **VSCode snippets**: Custom JSONC snippets

### Terminal & System Tools:
- **Tmux**: Custom keybindings, Dracula theme, TPM plugin manager, vim mode, mouse support
- **PowerShell**: Cross-platform profile, oh-my-posh, dotnet completions, fnm integration
- **Ghostty terminal**: Custom font size, themes, window dimensions
- **SSH**: Machine-specific key configurations, keychain integration

### Package Management:
- **macOS**: Brewfile with 20+ packages and casks
- **Windows**: Winget + Scoop packages (dual package manager setup)
- **Linux/RPi**: APT + Snap packages (dual package manager setup)

### Custom Aliases & Functions (20+):
- `zsh::reload`, `zsh::update`, `zsh::clean`
- `brew::update`, `brew::cleanup`
- `ssh::gen-key`, `ssh::copy`, `ssh::fix-keychain`
- `cat` → `bat`, `vim` → `nvim`, `ls` → `eza`
- Machine-specific functions: `profile`, `zip-encrypt`, `unzip-encrypt`, `temp` (RPi temperature)
- Utility functions: `env::load`, `venv::activate`, `zsh::time`

### Private Data Management:
- **API Keys**: OpenAI, Anthropic, GitHub, Figma, Telegram bots, Serper, Apify, YouTube, OANDA, Tavily
- **SSH Keys**: Multiple keys (github.key, personal.key, ssh.key) with .pub counterparts
- **Service Tokens**: Tailscale authkey, GitHub registry token

### System Preferences (macOS):
- **13 different system defaults**: Hostname, dock settings, trackpad, keyboard, window behavior
- **Touch ID for sudo** setup
- **PAM configuration** modifications

### Machine-Specific Customizations:
- **macOS**: iCloud paths, Developer directory, Godot path, pyenv shims
- **Windows**: Different SSH key (personal.key vs ssh.key)
- **RPi**: Snap bin path, temperature monitoring, RPi-specific update commands

## ANALYSIS:
- **Total config lines**: ~500+ lines across all files
- **Environment variables**: 25+ custom environment variables
- **Zsh plugins**: 6+ different plugins with complex configurations
- **Custom functions**: 20+ shell functions
- **Package managers**: 6 different package management systems
- **XDG compliance**: 14 custom directory paths following XDG spec

## DESIGN DECISIONS NEEDED:

### 1. Config Engine/Merge Strategy:
Currently leaning toward **runtime sourcing** (generated template files that source base + machine configs) rather than file generation/merging. This keeps configs readable and debuggable.

### 2. Package Management:
Need to handle 6 different package managers with different syntax:
- **Brewfile** (standard format)
- **Winget** (YAML or command list?)
- **Scoop** (JSON or command list?)
- **APT** (simple package list)
- **Snap** (simple package list)
- **MAS** (ID-based App Store installs)

### 3. Tool/Plugin Logic Beyond File Linking:
Some tools require commands beyond just linking files:
- **SSH**: Key generation, keychain setup, server configuration
- **System Preferences**: Running macOS defaults commands
- **Package Installation**: Different syntaxes for different managers
- **Service Setup**: Tailscale, Docker, etc.

### 4. Cross-Platform Shared Logic:
Some logic is shared across Unix systems but not Windows:
- **Shell configuration**: Zsh on macOS/Linux, PowerShell on Windows
- **SSH setup**: Different key names per machine
- **Package managers**: Brew works on macOS/Linux, Winget/Scoop on Windows

### 5. Minimal Implementation Target:
Goal is ~200 lines of Python that preserves all current functionality while being radically simpler than the current 2,700+ line system.

## FINAL DESIGN DECISIONS:

### Architecture: Hybrid Python + Shell Scripts
- **Python CLI**: Clean interface, logging, error handling, file operations
- **Shell Scripts**: Platform-specific setup logic (avoid cross-platform Python mess)
- **Package Management**: Consolidated files (apt.pkg, brewfile) with unified parser
- **Config Engine**: Runtime sourcing via generated template files

### CLI Interface:
```bash
# Main workflow (with machine auto-detection via $MACHINE env var)
machine setup [--private-dir PATH] [--dry-run]
machine update [--dry-run]

# Explicit machine specification
machine setup macbook-personal --private-dir PATH

# Individual tools (if simple to maintain)
machine ssh setup [--dry-run]
machine git setup [--dry-run]
```

### New Minimal Structure:
```python
app/
├── cli.py          # Main commands & CLI interface
├── machine.py      # Machine detection & config loading
├── packages.py     # Package file parsing & installation
├── files.py        # File linking logic
├── private.py      # Private files handling
└── utils.py        # Shell execution, logging
```

### Config Structure:
```
config/
├── base/           # Cross-platform base configs
│   ├── gitconfig, zshrc, ps_profile.ps1
│   └── scripts/    # Shared setup scripts
└── macbook-personal/
    ├── files/      # Machine-specific config files
    ├── packages/   # brewfile, apt.pkg, etc.
    └── scripts/    # Machine-specific setup scripts
        ├── setup.sh    # Unix setup logic
        └── setup.ps1   # Windows setup logic
```

## NEXT STEPS TO COMPLETE:

### 0. Final Feature Comparison & Testing Cleanup
- [ ] Complete comparison of features against old repo
- [ ] Ensure tests are comprehensive and cleaned up
- [ ] Validate test machine works properly
- [ ] Verify dry-run mode works everywhere

### 1. Deployment & Production Polish
- [ ] Review and update deployment scripts in `scripts/`
- [ ] Ensure logging system matches old quality (Rich formatting, session separators)
- [ ] Verify production logging works identically to old system

### 1.5 Documentation Update
- [ ] Rewrite `README.md` to explain:
  - How to deploy a new machine
  - How to cleanup/update existing machines
  - How to manage local changes
  - How to define new tools
  - How to define new machines

### 2. Project Configuration Review
- [ ] Review and update `.github/` workflows
- [ ] Review `.vscode/` configurations
- [ ] Update `.gitignore` for new structure
- [ ] Review `.pre-commit-config.yaml`
- [ ] Update `pyproject.toml` for new app structure

### 2.5 Development Documentation
- [ ] Update README with development setup instructions
- [ ] Document the simplified architecture
- [ ] Create contribution guidelines

## IMPLEMENTATION STATUS:
- **✅ ARCHITECTURE COMPLETE**: New minimal CLI structure implemented under `app_new/`
- **✅ CORE FUNCTIONALITY**: Machine detection, config linking, package parsing, private files all working
- **✅ ENHANCED UTILITIES**: Advanced logging with file rotation, loading indicators, shell execution, recursive linking, environment variable loading, platform detection
- **✅ TEMPLATE GENERATION**: File generation with {MACHINE} and {MACHINE_ID} substitutions for .gitconfig, .zshenv, .zshrc, ps_profile.ps1
- **✅ TOOL-SPECIFIC LOGIC**: Simple tools.py module with SSH, VSCode setup and individual tool commands
- **✅ SHELL SCRIPTS**: Platform-specific scripts created:
  - macOS: ssh-server.sh, touch-id.sh, xcode.sh, system-preferences.sh
  - Linux: ssh-server.sh, user-shell.sh, user-config.sh, ssh-keygen.sh, vscode-tunnel.sh
- **✅ CLI COMMANDS**: setup, update, ssh (setup/keygen), vscode (setup/tunnel), git (setup)
- **✅ TESTS**: Comprehensive test suite in `tests_new/` - all functionality validated
- **✅ IMPROVED DESIGN**: Auto-discovery for tools, better test machine template, enhanced locality
- **✅ READY FOR USE**: All core functionality preserved in ~400 lines vs original 2,700+ lines
