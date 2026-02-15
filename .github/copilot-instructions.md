# Dev Machine (`mc`)

Cross-platform machine bootstrapper and dotfile manager.

## Tech Stack

- **Language**: Python 3.14+
- **CLI**: Typer + Rich
- **Config**: Pydantic Settings, YAML manifests
- **Packaging**: uv (build, lock, tool install)
- **Linting**: Ruff (line-length 88, rules: E, I, W, RUF)
- **Type checking**: Pyright (standard mode)

## Project Layout

- `src/machine/` - Python package (CLI app)
- `config/` - Shared dotfiles and configs
- `machines/` - Per-host configurations
- `bootstrap.sh` / `bootstrap.ps1` - Bare-machine bootstrap

## Commands

- `uv sync --dev` - Set up dev environment
- `uv run mc --help` - Run CLI in dev
- `uv run ruff check src/` - Lint
- `uv run pyright src/` - Type check
