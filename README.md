# Machine Setup & Dotfiles

Cross-platform dotfiles and environment manager for macOS, Windows, and Linux.

## Requirements

- `git`
- `uv`

**macOS:**

```sh
xcode-select --install # installs git
```

**Windows:**

```powershell
winget install Microsoft.Powershell
winget install Git.Git
winget install astral-sh.uv
```

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

> Repository path can be overridden with `$MC_ROOT`.
