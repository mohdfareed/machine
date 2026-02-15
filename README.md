# Machine Setup & Dotfiles

Cross-platform dotfiles and environment manager for macOS, Windows, and Linux.

## Requirements

- `git` (must be installed manually on Linux)
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

> On Windows, `uv` is managed via `winget`. On Unix, if `uv` is not found,
> it will be installed to `~/.local/bin` and added to the PATH in `~/.zshenv`.
> `~/.zshenv` is sourced and the PATH is checked before modifications.

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
