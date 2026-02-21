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
mc setup <machine> [modules]   Deploy configs, packages, and scripts
mc update                      Pull latest repo changes
mc upgrade [modules]           Run upgrade scripts
mc info / list / show          Display machine info
```

Run `mc -h` or `mc <command> -h` for full options.

## Design

```
~/.machine/
├── config/                  ← shared modules (git, shell, …)
│   └── <name>/
│       ├── module.py        ← Module(files, packages, scripts)
│       └── …
├── machines/                ← per-host manifests
│   └── <id>/
│       ├── manifest.py      ← MachineManifest(name, modules, files, packages, scripts, env)
│       └── …
└── src/machine/             ← CLI (core.py, app.py, cli.py, manifest.py)
```

**Modules** (`config/<name>/module.py`) export a `Module`:

| Field          | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| `files`        | `FileMapping(source, target)` → symlinked to `~`                    |
| `packages`     | `Package(name, brew=, apt=, snap=, winget=, scoop=, mas=, script=)` |
| `scripts`      | Platform-tagged scripts to run                                      |
| `overrides`    | Local override files: `{filename: target}`                          |
| `depends`      | Module names that must be included before this                      |
| `required_env` | Env vars the manifest must provide                                  |

**Manifests** (`machines/<id>/manifest.py`) export a `MachineManifest`:

| Field      | Description                                    |
| ---------- | ---------------------------------------------- |
| `name`     | Public display name; defaults to machine ID    |
| `modules`  | Module names to compose                        |
| `files`    | Machine-specific symlinks                      |
| `packages` | Machine-specific packages                      |
| `scripts`  | Machine-specific scripts                       |
| `env`      | Env vars injected into all script subprocesses |

**Platform tags** on script filenames filter by platform — no tag means all platforms:

| Tag      | Runs on                 |
| -------- | ----------------------- |
| `.macos` | macOS                   |
| `.linux` | Linux                   |
| `.unix`  | macOS, Linux, WSL, GHCS |
| `.win`   | Windows                 |
| `.wsl`   | WSL                     |
| `.ghcs`  | GitHub Codespaces       |

**Script prefixes** control execution behavior:

| Prefix     | Behavior                                 |
| ---------- | ---------------------------------------- |
| `init_`    | Runs before packages (env/tool setup)    |
| `once_`    | Runs once per machine, then skipped      |
| `watch_`   | Reruns when the script's content changes |
| `upgrade_` | Runs only during `mc upgrade`            |

**Env vars** are injected into every script subprocess at runtime — never written to files:

- `MC_HOME`: The root directory of the machine config (e.g., `~/.machine`)
- `MC_ID`: The machine ID (e.g., `my-laptop`)
- `MC_NAME`: The machine name (defaults to `MC_ID`), can be overridden in manifest
- `MC_USER`: The current user name

**SSH keys:** the `ssh` module reads `MC_PRIVATE` from env, copies keys to `~/.ssh/`, sets permissions, and adds them to the agent. Skips silently if `MC_PRIVATE` is unset.

**Local overrides:** modules declare which `*.local` files they accept via the `overrides` field. Drop matching files in your machine dir and they are auto-discovered and symlinked:

- `~/.gitconfig.local` — declared by `git` module, included by gitconfig
- `~/.zshenv.local` — declared by `shell` module, sourced by zshenv
- `~/.zshrc.local` — declared by `shell` module, sourced by zshrc
- `~/.zshrc.local` — declared by `shell` module, sourced by zshrc
- `~/term.settings.json` — declared by `win-term` module, used by Windows Terminal

## Development

```sh
cd ~/.machine

# build and run
uv sync --dev
uv run mc --help

# format, lint, test
./scripts/test.sh
```
