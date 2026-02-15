# Machine Setup & Dotfiles

Cross-platform dotfiles and environment manager for macOS, Windows, and Linux.

## Requirements

- `git`
- `uv`

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

> Repository path can be overridden with `$MC_HOME`, defaulting to `~/.machine`.

Re-install the CLI tool on an existing machine:

```sh
# Unix (macOS/Linux)
. $MC_HOME/bootstrap.sh
```

```powershell
# Windows
. $MC_HOME\bootstrap.ps1
```

## Development

Set up the development environment and run the CLI tool:

```sh
cd $MC_HOME
./scripts/run.sh --help
```
