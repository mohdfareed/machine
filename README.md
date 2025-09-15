# Machine Setup & Dotfiles

## Requirements

- Python 3.8+
- Xcode Command Line Tools (macOS)
- PowerShell 7.0+ (Windows)

Xcode Command Line Tools can be installed with:

```sh
xcode-select --install
sudo xcodebuild -license accept
```

Windows can install Python and PowerShell from the Microsoft Store or using:

```powershell
winget install Python.Python3.12 # 3.8+
winget install Microsoft.Powershell # 7.0+
```

## Installation

Run the following command to install Chezmoi and bootstrap a machine:

```sh
repo="https://raw.githubusercontent.com/mohdfareed/machine/refs/heads/main"
curl -fsLS "$repo/bootstrap.py" | python3 - [-h] <path> [args...]
```

```powershell
$repo = "https://raw.githubusercontent.com/mohdfareed/machine/refs/heads/main"
curl -fsLS "$repo/bootstrap.py" | python3 - [-h] <path> [args...]
```

where,

- `-h` or `--help` shows the help message.
- `<path>` is where the machine will be set up (default: `~/.machine`).
- `args...` are extra arguments passed to Chezmoi.

## Usage (Chezmoi)

```sh
chezmoi init --apply   # apply machine config
chezmoi apply          # reapply machine config
chezmoi update         # update repo and reapply config
chezmoi status         # show status of the config
code $MACHINE          # open repo in vscode
```

## Scripts & Phases
- Put shared scripts in `config/scripts/` and machine-specific in `machines/<id>/scripts/`.
- OS suffixes are respected: `*.macos.sh`, `*.linux.sh`, `*.win.ps1`, `*.unix.sh`.
- Phases are triggered by filename prefixes via Chezmoi:
  - `before_*` → runs before apply
  - `after_*` → runs after apply
  - `once_*` → runs only once
  - `onchange_*` → runs when content changes
- Package installs: editing `config/packages.yaml` or `machines/<id>/packages.yaml` triggers an `onchange_*` script that installs packages.

Tip: to test scripts manually, run the underlying script files directly from `config/scripts/` or `machines/<id>/scripts/`.

## Machine Settings
- Variables used across the system:
  - `MACHINE`: repo root (e.g., `~/.machine`)
  - `MACHINE_ID`: selected machine profile (e.g., `macbook`)
  - `MACHINE_SHARED`: `config/`
  - `MACHINE_CONFIG`: `machines/<id>/`
  - `MACHINE_PRIVATE`: path to private files (default `~/.private`)
- How they’re set:
  - Chezmoi template `.chezmoi.toml.tmpl` prompts/uses env on first apply.
  - Shell profiles (`.zshenv`, `profile.ps1`) export them for interactive shells.
  - Script runner passes these vars to Python scripts so phase scripts have consistent context.
- Priority concept:
  - When running scripts manually, pass explicit args/env if needed.
  - When running via Chezmoi phases, the template context provides the authoritative values.

### Machine Backup

- Review installed apps.
- Review config.
- Commit changes to repo.

## TODO

- Hostname configuration
- Share passwords/secrets with other machines
- Add script as CLI interface to Chezmoi operations

- SSH:
  - Load ssh keys from private dir and set permissions
  - Add keys to agent
  - Keychain integration
  - Key pair generation
  - Add keys to authorized_keys

- Windows:
  - WSL support
  - Terminal configuration
  - Test line endings with unix-based repos
  - [Steam Rom Manager](https://steamgriddb.github.io/steam-rom-manager/)

- CI/CD:
  - Restore python formatting checks in ci
  - Add update script for updating dependencies during cd

- Updating scripts:
  - Package managers
  - `zinit`
  - Theme on linux
