# Dev Machine (`mc`)

Cross-platform machine bootstrapper and dotfile manager.

> **Agent instruction:** This file contains project-specific conventions,
> constraints, and preferences that shape how you work on this codebase.
> When the user states a preference or rule ("never do X", "always use Y"),
> add it here. When the project changes in a way that contradicts an existing
> note, update or remove it. Do this proactively — don't wait to be asked.
>
> For cross-session memory (context from previous conversations), use the
> `machine-memories` MCP tool. This file is for durable coding standards, not
> session notes.
>
> ALWAYS ensure the README.md, AGENTS.md, and the memories MCP tool are
> consistent and up-to-date with the latest project conventions and rules.

## Tech Stack

- **Language**: Python 3.14+
- **CLI**: Typer + Rich
- **Config**: Pydantic models, Python manifests
- **Packaging**: uv (build, lock, tool install)
- **Linting**: Ruff (line-length 100, rules: E, I, W, RUF)
- **Type checking**: Pyright (standard mode)

## Project Layout

- `src/machine/` - Python package (CLI app)
- `config/` - Shared dotfiles and configs
- `machines/` - Per-host configurations
- `bootstrap.sh` / `bootstrap.ps1` - Bare-machine bootstrap

## Architecture

### Module (`config/<name>/module.py`)

Exports a `Module(files, packages, scripts, depends)`. Files are symlinked,
packages installed via platform manager, scripts run with tracking.
Scripts under `scripts/` are auto-discovered; explicit `scripts=` list
is only needed for files outside that directory. `depends=["other"]`
auto-includes prerequisite modules in manifests (deduped, ordered before
the dependent).

### Manifest (`machines/<id>/manifest.py`)

Exports a `MachineManifest(modules, files, packages, scripts, env)`.
Composes modules and adds machine-specific overrides. `env` dict is
passed to scripts at runtime (not written to files).

### Cross-Platform Requirements

- Always verify Windows compatibility when touching files, paths, or scripts
- Windows SSH client is OpenSSH (built into Windows 10+): supports `~`, `IgnoreUnknown`
- Shell scripts need platform tags (`.unix.sh` / `.win.ps1`) — never assume Unix-only
- Path separators: use `pathlib.Path` in Python; avoid hardcoded `/` in target strings

### Key Conventions

- Before writing new code, check the codebase for existing patterns and follow them
- No generated env files — shell configs are static, committed files
- Platform tags on scripts: `name.macos.sh`, `name.unix.sh`, `name.win.ps1`
- Script prefixes: `once_` = run once, `watch_` = re-run on file change, `init_` = run before packages, `upgrade_` = run only during `mc upgrade`, `_` = helper (never auto-executed, sourced by other scripts)
- Execution order: files → `init_*` scripts → packages → remaining scripts
- Machine extras: `extra.zsh` → `~/.zshrc.local`
- Repo root derived from `Path(__file__).parents[2]` — no env var needed
- App data: `typer.get_app_dir("mc")` for logs/state
- State file: `~/.local/share/mc/state.json` tracks installed packages and script runs
- Secrets: `MC_PRIVATE/env/<MC_ID>.env` symlinked → `~/.env`; plain dotenv format (no `export`)
- CLI path helpers: `mc home` prints MC_HOME, `mc private` prints MC_PRIVATE (pipe to `code`)

## Commands

- `./scripts/test.sh` - Lint, format, and type check (always use this to validate)
- `./scripts/run.sh --help` - Run CLI in dev
