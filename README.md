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

## Scripting
- Put shared scripts in `config/scripts/` and machine-specific in `machines/<id>/scripts/`.
- OS suffixes are respected: `*.macos.sh`, `*.linux.sh`, `*.win.ps1`, `*.unix.sh`.
- Phases are triggered by filename prefixes via Chezmoi:
  - `before_*` → runs before apply
  - `after_*` → runs after apply
  - `once_*` → runs only once
  - `onchange_*` → runs when content changes
- Package installs: editing `config/packages.yaml` or `machines/<id>/packages.yaml` triggers an `onchange_*` script that installs packages.

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

### Machine Backup

- Commit and push changes to local repositories.
- Review installed apps and their configurations.
- Review machine config files.

## SSH Setup

- Add keys: place your keys in `$MACHINE_PRIVATE/ssh/`.
  - Example: `personal` + `personal.pub`.
- Configure SSH: edit `machines/<id>/ssh.config` for per‑machine settings.

## TODO

- Hostname configuration (prompt, default to machine_id.local)
- Share passwords/secrets with other machines (iCloudDrive?)
- Package managers priority per os (or machine) to de-duplicate installs

- SSH:
  - [x] Load ssh keys from private dir and set permissions
  - [x] Create `~/.ssh/config` and `~/.ssh/authorized_keys` with proper permissions
  - [x] Add keys to agent (macOS/Linux/Windows)
  - [ ] Keychain integration enhancements (macOS) — e.g., service tweaks

- Windows:
  - WSL support
  - Terminal configuration
  - fix authorized_keys config and aliases
  - Test line endings with unix-based repos

- CI/CD:
  - Restore python formatting checks in ci
  - Add update script for updating dependencies during cd

- Updating scripts:
  - Package managers
    - Manual scripts
  - `zinit`
  - `nvim` (lazy vim)
