# Refactoring Plan

Cross-platform environment bootstrapper → proper `uv`-managed Typer CLI app.

This document tracks the full refactoring plan for implementers. Each phase is
self-contained, ordered by dependency. Check off steps as they are completed.

---

## Phase 1: Dev Setup & Project Infrastructure

> **Goal**: Transform the repo into a proper Python project with `pyproject.toml`,
> `uv` tooling, and CI — before touching any application code. The app can be a
> hello-world stub; the point is getting the skeleton right.

### 1.1 Bootstrap / Deployment Model

**Problem solved**: The old approach used raw `setup.py` (argparse, no
packaging), required Python 3.8 on the system, and had fragile `sys.path`
manipulation. The new model uses `uv tool install` for fully isolated
deployment.

**Bootstrap flow** (for a bare machine):

```
curl -LsSf https://astral.sh/uv/install.sh | sh   # installs uv (static binary)
git clone https://github.com/mohdfareed/machine ~/.machine
uv tool install ~/.machine                          # installs `mc` CLI in isolated env
```

- `uv` downloads Python 3.14 automatically if not present
- The CLI executable is symlinked to `~/.local/bin/mc` (Unix) or equivalent
  (Windows) — already on PATH after `uv tool update-shell`
- The cloned repo remains at `~/.machine` for configs/dotfiles (the CLI reads
  from it at runtime)
- Updating: `cd ~/.machine && git pull && uv tool install . --reinstall`
- No system Python pollution, no manual venv, no PATH hacking

**Windows equivalent**:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
git clone https://github.com/mohdfareed/machine $HOME/.machine
uv tool install $HOME/.machine
```

**Decision**: `uv tool install` over `pipx` — uv is already a project
dependency and can self-bootstrap Python. One less tool.

### 1.2 Create `pyproject.toml`

Create at repo root. Follow `kbm` conventions:

```toml
[project]
name = "mc"
version = "0.1.0"
description = "Cross-platform machine bootstrapper and dotfile manager."
readme = "README.md"
license-files = ["LICENSE*"]
requires-python = ">=3.14"
dependencies = [
    "typer>=0.21",
    "rich>=14.0",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pre-commit>=4.0",
    "pyright>=1.1",
    "ruff>=0.14",
]

[project.scripts]
mc = "mc.cli:main"

[build-system]
requires = ["uv_build>=0.9,<0.11"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = ["mc"]

[tool.ruff]
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = ["E", "I", "W", "RUF"]

[tool.pyright]
pythonVersion = "3.14"
typeCheckingMode = "standard"
useLibraryCodeForTypes = true
```

**Key decisions**:

| Choice        | Value               | Rationale                                |
| ------------- | ------------------- | ---------------------------------------- |
| Package name  | `mc`                | Short, memorable CLI name                |
| Python        | `>=3.14`            | User wants bleeding edge; uv handles it  |
| Build backend | `uv_build`          | Matches kbm, native uv support           |
| Line length   | 88                  | Matches kbm (was 79, now standard black) |
| Ruff rules    | E, I, W, RUF        | Matches kbm                              |
| Type checker  | pyright std         | Matches kbm                              |
| Dependencies  | typer, rich, pyyaml | Minimal — only what the CLI needs        |

### 1.3 Create Source Layout

Rename `src/` → `src/mc/` (proper `src` layout per kbm):

```
src/mc/
├── __init__.py         # version import via importlib.metadata
├── __main__.py         # `python -m mc` support
└── cli/
    └── __init__.py     # Typer app, main(), hello world stub
```

The old `src/*.py` files (`core.py`, `dotfiles.py`, etc.) will be migrated in
later phases. For now, the stub CLI just prints hello world to validate the
packaging pipeline.

**`src/mc/__init__.py`**:

```python
from importlib.metadata import version
__version__ = version("mc")
```

**`src/mc/__main__.py`**:

```python
from mc.cli import main
main()
```

**`src/mc/cli/__init__.py`**:

```python
import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def main(version: bool = typer.Option(False, "--version", "-v")) -> None:
    if version:
        from mc import __version__
        typer.echo(f"mc {__version__}")
        raise typer.Exit()
    # Default: show help
```

### 1.4 Create `.python-version`

```
3.14
```

Single file, tells uv which Python to use for development.

### 1.5 Generate `uv.lock`

Run `uv lock` to create the lockfile. Commit it to the repo. CI will use
`uv sync --dev --locked` to enforce lock freshness.

### 1.6 Update `.gitignore`

Replace current contents:

```gitignore
__pycache__/
.venv/
.ruff_cache/
.pytest_cache/
.coverage

*.egg-info/

# Editor/OS
.DS_Store

# Project-specific
lazy-lock.json
rag_storage/
```

### 1.7 Update `.editorconfig`

Current is fine. No changes needed:

```ini
root = true

[*]
indent_style = space
indent_size = 4
trim_trailing_whitespace = true
insert_final_newline = true

[*.{json,yaml,yml,toml}]
indent_size = 2
```

### 1.8 Update `.pre-commit-config.yaml`

Update to match kbm conventions (drop `--line-length=79`, use new defaults):

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.11
    hooks:
      - id: ruff-check
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

### 1.9 Update `.vscode/settings.json`

Add/update Python tooling settings to match new project:

```jsonc
{
    // existing settings stay...
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "ruff.lineLength": 88,
    // keep existing shellcheck, cSpell, Lua, MCP settings
}
```

- Change `ruff.lineLength` from implicit 79 to explicit 88
- Add pytest config

### 1.10 Update `.vscode/extensions.json`

Add pyright extension:

```jsonc
{
    "recommendations": [
        "donjayamanne.python-extension-pack",
        "charliermarsh.ruff",
        "ms-python.pyright",
        "ms-vscode.powershell",
        "timonwong.shellcheck",
        "yzhang.markdown-all-in-one",
        "streetsidesoftware.code-spell-checker",
        "github.copilot-chat"
    ]
}
```

### 1.11 Update `.github/copilot-instructions.md`

Expand with project conventions (tool name, tech stack, commands) so Copilot
has context. Reference kbm's version for style.

### 1.12 Rewrite CI (`.github/workflows/ci.yml`)

Replace the current 3-job workflow (compile-3.8 + ruff + shellcheck +
spelling) with a `uv`-native pipeline matching kbm:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-python: true
      - uses: actions/cache@v5
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
      - run: uv sync --dev --locked
      - name: Check formatting
        run: uv run ruff format --check src/
      - name: Run linter
        run: uv run ruff check src/
      - name: Run type checker
        run: uv run pyright src/

  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: ludeeus/action-shellcheck@master
        env:
          SHELLCHECK_OPTS: -e SC1071

  spelling:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: reviewdog/action-misspell@master
        with:
          github_token: ${{ secrets.github_token }}
          reporter: github-check
          level: warning
          locale: "US"
          exclude: |
            *.lock
```

**Changes from current CI**:

- ~~Python 3.8 compile check~~ → replaced by `uv sync --locked` (validates
  against `requires-python = ">=3.14"`)
- ~~Standalone ruff action~~ → `uv run ruff` (uses locked version)
- **Added**: pyright type checking
- **Kept**: shellcheck, spelling (unchanged)
- Line length now 88 (via pyproject.toml, not CLI arg)

### 1.13 Rewrite CD (`.github/workflows/cd.yml`)

Update to use `uv` instead of bare `pip install pre-commit`:

```yaml
name: CD

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - name: Set up environment
        uses: ./.github/setup
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Update pre-commit hooks
        run: |
          uv tool install pre-commit
          pre-commit autoupdate

      - name: Create pull request
        uses: peter-evans/create-pull-request@main
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "chore: update dependencies"
          title: "Update dependencies"
          branch: "deps"
          sign-commits: true
          labels: "CD"
```

### 1.14 Update `dependabot.yml`

Add `uv` ecosystem (for `uv.lock` updates):

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "deps:"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      github-actions:
        patterns:
          - "*"
```

### 1.15 Delete Old Dev Scripts

Remove files that are replaced by `uv` + `pyproject.toml`:

| File           | Reason for deletion                               |
| -------------- | ------------------------------------------------- |
| `setup.sh`     | Replaced by `uv sync --dev`                       |
| `update.sh`    | Replaced by `pre-commit autoupdate` + CD workflow |
| `__pycache__/` | Should already be gitignored                      |

The old `setup.py` (main CLI entrypoint) will be removed in a later phase once
the Typer CLI in `src/mc/cli/` is built out. For now it can coexist.

### 1.16 Clean Up `.github/.github.example/`

This directory contains kbm example configs — remove it. The project now has
its own proper CI/CD configs.

### 1.17 Add LICENSE

Currently missing. Add an MIT `LICENSE` file (matching kbm).

### 1.18 Verification

After completing Phase 1:

```sh
# Dev setup (one command)
uv sync --dev

# Run the stub CLI
uv run mc --version      # → mc 0.1.0
uv run mc --help         # → shows help
python -m mc --version   # → mc 0.1.0 (via __main__.py)

# Lint & type check
uv run ruff check src/
uv run ruff format --check src/
uv run pyright src/

# Install as tool (simulates deployment)
uv tool install .
mc --version             # → mc 0.1.0

# Pre-commit
uv run pre-commit run --all-files

# CI should pass on push
```

---

## Phase 2+: Application Code Migration (Future)

> These phases are outlined here for visibility but will be planned in detail
> after Phase 1 is complete.

### Phase 2: Core Module & Platform Detection

- Migrate `core.py` → `src/mc/core.py`
- Modernize: `match` statements, proper enums, type hints with 3.14 syntax
- Replace global mutable state (`set_dry_run`/`set_debug`) with context or
  config object
- Add Typer global options (`--dry-run`, `--debug`) via app callback

### Phase 3: Package Management

- Migrate `packages.py` → `src/mc/commands/packages.py` (or `plugins/`)
- `mc install` command
- YAML manifest loading with pydantic validation

### Phase 4: Dotfile Management

- Migrate `dotfiles.py` → `src/mc/commands/dotfiles.py`
- `mc dotfiles` command
- Symlink deployment, template rendering, backup logic

### Phase 5: Script Engine

- Migrate `scripts.py` + `state.py` → `src/mc/commands/scripts.py`
- `mc scripts` command
- Platform filtering, phased execution, once/onchange tracking

### Phase 6: SSH Key Management

- Migrate `ssh.py` → `src/mc/commands/ssh.py`
- `mc ssh` command

### Phase 7: Update System

- Migrate `update.py` → `src/mc/commands/update.py`
- `mc update` command

### Phase 8: Orchestration & Bootstrap

- `mc setup <machine_id>` — replaces old `setup.py` entrypoint
- Bootstrap script (`bootstrap.sh` / `bootstrap.ps1`) — the curl one-liner
- Remove old `setup.py`

### Phase 9: README, Docs & Polish

- Rewrite README for new CLI
- Auto-generate CLI docs via `typer`
- Final cleanup

---

## Reference: Current File Inventory

### Python Source (`src/` — to become `src/mc/`)

| File          | Purpose                                   | Lines |
| ------------- | ----------------------------------------- | ----- |
| `__init__.py` | Re-exports from core                      | ~10   |
| `core.py`     | Platform detection, enums, run(), logging | ~200  |
| `dotfiles.py` | Symlinks, template generation             | ~405  |
| `packages.py` | YAML loading, package installation        | ~100  |
| `scripts.py`  | Script discovery, filtering, execution    | ~150  |
| `ssh.py`      | SSH key copy, agent, permissions          | ~120  |
| `state.py`    | JSON state persistence for scripts        | ~80   |
| `update.py`   | Package/plugin/editor updates             | ~80   |

### Config (`config/`)

| Path                           | What it configures                     |
| ------------------------------ | -------------------------------------- |
| `packages.yaml`                | Shared package manifest (all managers) |
| `ghostty.config`               | Ghostty terminal (macOS)               |
| `terminal.win.json`            | Windows Terminal settings              |
| `git/.gitconfig`               | Shared git config (identity, signing)  |
| `git/.gitconfig.windows`       | Windows line-ending overrides          |
| `git/.gitconfig.wsl`           | WSL credential helper                  |
| `git/.gitignore`               | Global gitignore                       |
| `shell/zshenv`                 | Shared zsh environment                 |
| `shell/zshrc`                  | Shared zsh interactive config          |
| `shell/aliases.sh`             | Zsh aliases & functions                |
| `shell/profile.ps1`            | PowerShell profile                     |
| `shell/aliases.ps1`            | PowerShell aliases                     |
| `vim/init.lua`                 | Neovim bootstrap (lazy.nvim + LazyVim) |
| `vim/lazyvim.json`             | LazyVim extras config                  |
| `vim/lazy-lock.json`           | Pinned plugin versions                 |
| `vim/lua/config/options.lua`   | Neovim options                         |
| `vim/lua/plugins/core.lua`     | Theme, UI plugin configs               |
| `vim/lua/plugins/lazydev.lua`  | Lua dev environment                    |
| `vscode/settings.json`         | VS Code settings                       |
| `vscode/keybindings.json`      | VS Code keybindings (empty)            |
| `vscode/mcp.json`              | VS Code MCP servers (empty)            |
| `vscode/prompts/beast-mode...` | Copilot Chat agent mode                |
| `vscode/snippets/jsonc.json`   | JSONC snippets                         |
| `scripts/brew.unix.sh`         | Homebrew install/update                |
| `scripts/setup.macos.sh`       | macOS hostname + SSH                   |
| `scripts/setup.linux.sh`       | Linux hostname + SSH server            |
| `scripts/setup.linux.wsl.sh`   | WSL shell + apt                        |
| `scripts/setup.win.ps1`        | Windows features + SSH server          |
| `scripts/once_vscode-tunnel.*` | VS Code tunnel service (one-time)      |

### Machines (`machines/`)

| Machine      | Platform  | Key overrides                                                       |
| ------------ | --------- | ------------------------------------------------------------------- |
| `macbook`    | macOS     | Brew+MAS pkgs, iCloud vars, Keychain SSH, system defaults, Touch ID |
| `pc`         | Windows   | Gaming+media pkgs, SSH server, Tailscale                            |
| `gleason`    | Windows   | Work dev pkgs (Go, .NET, Docker, Sysinternals)                      |
| `rpi`        | Linux     | Curl-installed pkgs, temp monitor, lingering                        |
| `codespaces` | Codespace | Disable commit signing only                                         |

### Dev/CI Files (`.github/`, root)

| File                              | Current purpose                 | Phase 1 action |
| --------------------------------- | ------------------------------- | -------------- |
| `.github/workflows/ci.yml`        | Compile 3.8, ruff, shell, spell | **Rewrite**    |
| `.github/workflows/cd.yml`        | Pre-commit update PR            | **Rewrite**    |
| `.github/setup/action.yml`        | Git author config               | Keep           |
| `.github/copilot-instructions.md` | Copilot context                 | **Expand**     |
| `.github/dependabot.yml`          | GH Actions updates              | **Add uv**     |
| `.github/.github.example/`        | kbm example configs             | **Delete**     |
| `.editorconfig`                   | Indent/whitespace rules         | Keep           |
| `.pre-commit-config.yaml`         | Ruff hooks                      | **Update**     |
| `.vscode/settings.json`           | Dev editor settings             | **Update**     |
| `.vscode/extensions.json`         | Recommended extensions          | **Update**     |
| `.vscode/mcp.json`                | MCP server config               | Keep           |
| `.gitignore`                      | Ignore patterns                 | **Update**     |
| `setup.sh`                        | Dev venv setup                  | **Delete**     |
| `update.sh`                       | Compile + pre-commit            | **Delete**     |
| `setup.py`                        | Old CLI entrypoint              | Keep (phase 8) |

---

## Reference: User Philosophy & Pain Points

Captured from prior discussions — these guide all design decisions:

**Philosophy**:

1. Tool must get out of the way — not become a project itself
2. Facilitate experimentation — easy, non-intimidating changes
3. Visibility & predictability — see what will happen before it does
4. Incremental changes — no all-or-nothing runs
5. Fearless runs — never disrupt manually-adjusted settings
6. Reuse across contexts — share configs between personal/work
7. No repetition — memory system for cross-session context

**Pain Points** (to address in later phases):

1. Fear of running the tool (might break manually-tweaked configs)
2. All-or-nothing setup (can't just tweak one thing)
3. Messy RPi Docker environment
4. Unsupported work machine (Gleason)
5. Setup opacity (can't see what will change)
6. Maintenance burden (tool requires frequent attention)
7. Context-switching between devices
8. Unclear project scope
