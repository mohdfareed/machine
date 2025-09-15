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


## Quickstart

After the initial bootstrap, use the lightweight CLI:

```sh
# from the repo root (e.g., ~/.machine)
bin/machine apply --machine macbook   # apply dotfiles + scripts
bin/machine update                    # pull + re-apply
bin/machine status                    # show pending changes
bin/machine packages --machine macbook# install packages
bin/machine run setup                 # run setup.* scripts
bin/machine run tunnel                # run tunnel.* scripts
```

These wrap `chezmoi` and re-use existing scripts, keeping behavior consistent.

## Usage (Chezmoi)

```sh
chezmoi init --apply # apply machine config
chezmoi update # update repo and reapply config
chezmoi status # show status of the config
code $MACHINE # open repo in vscode
```

### Machine Backup

- Review installed apps.
- Review config.
- Commit changes to repo.

## TODO

- Hostname configuration
- Share passwords/secrets with other machines

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
