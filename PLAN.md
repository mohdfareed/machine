# Simplification Plan

Cross-platform machine bootstrapper and dotfile manager.

## Decisions (Feb 2026)

These decisions supersede the phase-based refactoring plan below.

### Keep (earns its place)

- **Platform detection** (`StrEnum`, 44 lines) — needed for dotfile target
  paths, script filtering, shell selection. WSL/Codespaces detection can't use
  `sys.platform` alone.
- **Package model** (`Pydantic BaseModel`) — single cross-platform declaration
  (`brew="git", apt="git", winget="git.git"`) is the core value. Brewfile alone
  only covers macOS.
- **`once_`/`onchange_` script tracking** — cheap insurance (JSON state,
  ~20 lines). VS Code tunnel install isn't idempotent; this handles it.
- **Typer + Rich CLI** — discoverability via `--help`, autocomplete.
- **Pydantic models** for `Dotfile`, `Package`, `MachineManifest` — validation
  catches mistakes. Keep.
- **Logging** — reviewing post-setup output is useful. Wire up
  `setup_file_logging()` (currently dead code).

### Cut

- **`pydantic-settings`** — only binds 3 env vars (`MC_DEBUG`, `MC_DRY_RUN`,
  `MC_HOME`). Replace with `os.environ.get()` or a plain dataclass.
- **`BaseAppConfig`** — never subclassed. Dead code.
- **`setup_file_logging()` in current form** — defined but never called. Either
  wire it up or delete it.
- **`logs_path` computed field** — never referenced. Delete.
- **`_legacy/` directory** — delete entirely.
- **Python manifests via `importlib.util`** — replace with YAML manifests.
  Editor support via JSON schema instead of Python DSL.
- **Platform suffix filename convention** — scripts listed explicitly per
  machine in YAML manifest. No implicit convention to memorize.
- **Machine-specific `zshenv`/`zshrc` wrapper files** — machine vars go in YAML
  `env:` block (→ `~/.config/machine/env`), machine functions go in
  `machines/<id>/extra.zsh` (sourced by shared zshrc). Delete
  `machines/macbook/zshenv`, `machines/macbook/zshrc`, `machines/rpi/zshrc`.
- **Dead files** — empty `machines/gleason/profile.ps1`,
  duplicate `machines/macbook/packages.yaml` (manifest.py ignores it).

### Change

- **Machine manifests**: Python `manifest.py` → single YAML file per machine.
  Each YAML lists packages, dotfiles, env vars, scripts. No inheritance — repeat
  shared packages across machines (6 files, ~30 lines each, manageable).
- **App settings**: `pydantic-settings` → plain dataclass or `os.environ`.
- **Shell config**: 5 layers → 2 layers. Shared `zshrc`/`zshenv` +
  `~/.config/machine/env` (generated from YAML `env:` block). Machine-specific
  functions in `machines/<id>/extra.zsh`.
- **Script assignment**: filename suffix convention → explicit list in machine
  YAML. Machine file says what runs, no guessing.
- **Nvim config**: full LazyVim → minimal `init.lua` (~20 lines, syntax
  highlighting + line numbers, no plugin manager).
- **Services** (OpenClaw, OpenMemory): lightweight — scripts in
  `machines/<id>/scripts/` that run `docker run`/`docker compose`. Per-machine
  env vars in YAML `env:` block. No framework.

### New CLI commands

- `mc show <machine>` — print the full resolved config (packages, dotfiles,
  scripts, env).
- `mc list` — list all machines (scan `machines/` for YAML files).
- `mc setup <machine>` — apply config (existing, adapted for YAML).
- `mc update` — `git pull` + re-apply.

### Migration strategy

Build for `server` (new mac server) first. Deploy there, validate. Then migrate
`macbook`, then remaining machines.

### Machine YAML format

```yaml
packages:
  brew: [git, eza, bat, fzf, ripgrep]
  cask: [docker]
  apt: [git, eza, bat, fzf, ripgrep]

dotfiles:
  config/git/.gitconfig: ~/.gitconfig
  config/git/.gitignore: ~/.config/git/ignore
  config/shell/zshrc: ~/.zshrc
  config/shell/zshenv: ~/.zshenv
  config/ghostty.config: ~/.config/ghostty/config
  machines/server/ssh.config: ~/.ssh/config

env:
  MACHINE_ID: server

scripts:
  - config/scripts/brew.sh
  - once: machines/server/scripts/setup.sh
```

---

## Config Audit

Going through every config file, deciding what stays, what's cut, what's
simplified. Decisions tracked here as we go.

### Principle: never override tool defaults

Tools have default paths (Go → `~/go`, XDG → `~/.config`, etc.). Don't
override them with env vars just to move them. Overriding means you must
track both the var AND the default for every tool, on every machine. Use the
default, reference the default directly, done.

For PATH entries to tool binaries, guard with existence checks:
`[[ -d ~/go/bin ]] && export PATH="$HOME/go/bin:$PATH"`

### zshenv

- **XDG base dirs**: delete. They're already the defaults.
- **GOPATH override**: delete. Use Go's default `~/go`. Add `~/go/bin` to
  PATH with a directory guard.
- **PIP_REQUIRE_VIRTUALENV**: keep. Prevents accidental `pip install`.
