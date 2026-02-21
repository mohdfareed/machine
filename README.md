# Machine Setup & Dotfiles

Cross-platform dotfiles and machine manager for macOS, Windows, and Linux.

## Setup

Bootstrap a bare machine (installs `uv` and `git` if needed, clones repo, installs `mc`):

**Unix (macOS/Linux/WSL):**

```sh
curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.sh | sh
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.ps1 | iex
```

The repo is cloned to `~/.machine` by default. Override with `MC_HOME=<path>` before running.

Re-run bootstrap on an existing machine to reinstall the CLI after moving the repo:

```sh
~/.machine/bootstrap.sh
```

## Usage

```
mc setup <machine>    Deploy configs, install packages, run scripts
mc check [machine]    Validate manifests (env, files, scripts)
mc update [--stash]   Pull latest changes (--stash saves/restores local edits)
mc list               List available machines and modules
mc show <machine>     Show files, packages, scripts, and env for a machine
mc info               Show app paths and version
```

Global flags: `-n` / `--dry-run` (preview only), `-d` / `--debug`, `-v` / `--version`.

## Design

```
~/.machine/
├── config/                  ← shared modules (git, shell, …)
│   └── <name>/
│       ├── module.py        ← Module(files, packages, scripts)
│       └── …
├── machines/                ← per-host manifests
│   └── <id>/
│       ├── manifest.py      ← MachineManifest(modules, files, packages, scripts, env)
│       └── …
└── src/machine/             ← CLI (core.py, app.py, cli.py, manifest.py)
```

**Modules** (`config/<name>/module.py`) export a `Module`:

| Field       | Description                                      |
| ----------- | ------------------------------------------------ |
| `files`     | `FileMapping(source, target)` → symlinked to `~` |
| `packages`  | `Package(name, brew=, apt=, winget=, …)`         |
| `scripts`   | Platform-tagged scripts to run                   |
| `overrides` | Local override files: `{filename: target}`       |

**Manifests** (`machines/<id>/manifest.py`) export a `MachineManifest`:

| Field      | Description                                    |
| ---------- | ---------------------------------------------- |
| `modules`  | Module names to compose                        |
| `files`    | Machine-specific symlinks                      |
| `packages` | Machine-specific packages                      |
| `scripts`  | Machine-specific scripts                       |
| `env`      | Env vars injected into all script subprocesses |

**Platform tags** on script filenames control which scripts run:
`.macos`, `.linux`, `.unix`, `.win`, `.wsl`, `.ghcs`. No tag = all platforms.

**Script prefixes:** `once_` runs once per machine, `watch_` reruns when content changes, `init_` runs before packages.

**Env vars** (`MC_HOME`, `MC_ID`, `MC_NAME`, and manifest `env`) are injected at
runtime into script subprocesses — never written to files. `MC_NAME` defaults to
`MC_ID` and can be overridden via the manifest `name` field for a custom hostname
or tunnel display name.

**SSH keys:** the `ssh` module reads `MC_PRIVATE` from env, copies keys to `~/.ssh/`,
sets permissions, and adds them to the agent. Skips silently if `MC_PRIVATE` is unset.

**Local overrides:** modules declare which `*.local` override files they accept and
where they go (via the `overrides` field). Drop matching files in your machine dir
and they are auto-discovered and symlinked:

- `~/.gitconfig.local` — declared by `git` module, included by gitconfig
- `~/.zshenv.local` — declared by `shell` module, sourced by zshenv
- `~/.zshrc.local` — declared by `shell` module, sourced by zshrc

## Development

```sh
cd ~/.machine
uv sync --dev
uv run mc --help
```
