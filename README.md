# Machine Setup & Dotfiles

Cross-platform dotfiles and environment manager for macOS, Windows, and Linux.

## Requirements

- `git`
- `uv` (optional, installed with `curl` on bootstrap)
- Xcode Command Line Tools (macOS): `xcode-select --install`
- PowerShell (Windows): `winget install Microsoft.Powershell`

## Installation

Bootstrap a new machine:

```sh
# Unix (macOS/Linux)
curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.sh | sh
```

```powershell
# Windows
irm https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.ps1 | iex
```

> Repository path and branch can be overridden with `$MC_ROOT` and `$MC_BRANCH`, respectively.
