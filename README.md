# Machine Setup & Dotfiles

Cross-platform dotfiles and environment manager for macOS, Windows, and Linux.

```
config/              # Shared defaults (dotfiles, packages, scripts)
machines/<id>/       # Per-machine overrides
machine/             # Python automation module
setup.py             # Main entry point
```

## Requirements

- Python 3.8+
- Git
- Xcode Command Line Tools (macOS): `xcode-select --install`
- PowerShell 7.0+ (Windows): `winget install Microsoft.Powershell`

## Installation

Bootstrap a new machine:

```sh
# Unix (macOS/Linux)
curl -fsSL https://raw.githubusercontent.com/mohdfareed/machine/main/setup.py | python3 - <machine_id>

# Or clone and run
git clone https://github.com/mohdfareed/machine ~/.machine
cd ~/.machine && ./setup.py <machine_id>
```

```powershell
# Windows
iwr -useb https://raw.githubusercontent.com/mohdfareed/machine/main/setup.py | python -

# Or clone and run
git clone https://github.com/mohdfareed/machine $HOME/.machine
cd $HOME/.machine; python setup.py <machine_id>
```

## Usage

```sh
./setup.py --list                    # List available machines
./setup.py macbook                   # Full setup
./setup.py macbook --dry-run         # Preview changes
./setup.py macbook --update          # Update packages/plugins
./setup.py macbook --private ~/keys  # Specify private files path
```

### Selective Setup

```sh
./setup.py macbook --packages-only   # Only install packages
./setup.py macbook --dotfiles-only   # Only setup dotfiles
./setup.py macbook --scripts-only    # Only run scripts
./setup.py macbook --ssh-only        # Only setup SSH keys
```

## Configuration

### Machine Variables

Set automatically and available in shell:

| Variable | Description |
|----------|-------------|
| `MACHINE` | Repository root path |
| `MACHINE_ID` | Selected machine profile |
| `MACHINE_PRIVATE` | Path to private files |
| `MACHINE_SHARED` | Path to `config/` |
| `MACHINE_CONFIG` | Path to `machines/<id>/` |

### Packages

Edit `config/packages.yaml` (shared) or `machines/<id>/packages.yaml` (machine-specific):

```yaml
brew:
  - git
  - neovim
apt:
  - build-essential
  - script: curl -fsSL https://example.com/install.sh | bash
```

Supported managers: `brew`, `mas`, `apt`, `snap`, `winget`, `scoop`

### Scripts

Place scripts in `config/scripts/` (shared) or `machines/<id>/scripts/` (machine-specific).

**Platform filtering** via file suffixes:
- `setup.macos.sh` — runs only on macOS
- `setup.unix.sh` — runs on macOS, Linux, WSL
- `setup.win.ps1` — runs only on Windows

**Execution phases** via filename prefixes:
- `before_*` — runs before main setup
- `once_*` — runs only once (tracked in `~/.machine-state.json`)
- `onchange_*` — runs when script content changes
- `after_*` — runs after main setup

### SSH Keys

1. Place keys in `~/.machine-private/ssh/` (or custom `--private` path)
2. Run setup — keys are copied to `~/.ssh` with correct permissions
3. Keys are added to SSH agent (with macOS Keychain support)

### Dotfiles

Most configs are symlinked directly. Shell configs and `.gitconfig` are generated with embedded paths to support the layered loading pattern:

```
private config → shared config → machine config
```

## Development

```sh
./setup.sh           # Set up dev environment (venv, pre-commit)
./update.sh          # Update pre-commit hooks
```

## Architecture

```
setup.py             # CLI entry point
machine/
├── core.py          # Platform detection, package managers, utilities
├── dotfiles.py      # Symlinks and config generation
├── packages.py      # Package installation
├── scripts.py       # Script execution with phases
├── ssh.py           # SSH key management
├── state.py         # Run-once tracking
└── update.py        # System updates
```
