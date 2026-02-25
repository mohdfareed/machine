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
│       ├── manifest.py      ← MachineManifest(modules, files, packages, scripts, env)
│       └── …
└── src/machine/             ← CLI (core.py, app.py, cli.py, manifest.py)
```

**Modules** (`config/<name>/module.py`) export a `Module`:

| Field          | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| `files`        | `FileMapping(source, target)` → symlinked to `~`                    |
| `packages`     | `Package(name, brew=, apt=, snap=, winget=, scoop=, mas=, script=)` |
| `scripts`      | Platform-tagged scripts to run                                      |
| `overrides`    | `FileMapping(source, target)` → machine-local override symlinks     |
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
- `MC_HOSTNAME`: Optional machine hostname; set in manifest `env` to rename the host

**Local overrides:** modules declare which `*.local` files they accept via the `overrides` field. Drop matching files in your machine dir and they are auto-discovered and symlinked:

- `~/.gitconfig.local` — declared by `git` module, included by gitconfig
- `~/.zshenv.local` — declared by `shell` module, sourced by zshenv
- `~/.zshrc.local` — declared by `shell` module, sourced by zshrc
- `~/term.settings.json` — declared by `win-term` module, used by Windows Terminal

## Secrets (`MC_PRIVATE`)

Secrets are stored outside the repo in `MC_PRIVATE` — a machine-specific path
set in the manifest's `env` dict (e.g. `$ICLOUD/.machine` on macOS,
`$HOME/.machine` on Linux). The directory is never checked into git.

```
MC_PRIVATE/
├── env/
│   ├── homelab.env  ← homelab secrets
│   ├── tailscale.env← Tailscale keys
│   └── agents.env   ← AI agent keys (OPENAI_API_KEY, etc.)
├── ssh/
│   └── <MC_ID>      ← private key named after machine ID
│   └── <MC_ID>.pub  ← optional matching public key
└── docker/
    └── homepage.env  ← service-specific secrets (HOMEPAGE_VAR=…)
```

### How secrets flow

1. **Shell env** — `init_secrets.py` (shell module) provisions `~/.env` in two modes:
   - **Explicit**: when `MC_ENV_FILES` is set (space-separated, e.g. `"homelab tailscale
     agents"`), looks up each `<name>.env` in `MC_PRIVATE/env/` and concatenates them.
   - **Simple**: when `MC_ENV_FILES` is unset, falls back to `MC_PRIVATE/.env`.

   Uses plain dotenv format (no `export`).

2. **SSH keys** — `init_keys.py` (ssh module) copies a single key named `<MC_ID>` from
   `MC_PRIVATE/ssh/` into `~/.ssh/` and registers it with `ssh-add`. Skips gracefully
   when `MC_PRIVATE` is unset; errors if MC_PRIVATE exists but the key doesn't.

3. **Docker .env** — the `homelab` module's deploy script (`docker.unix.sh`) builds each
   service's `.env` by concatenating:
   - `~/.env` — shared keys (so you only define `OPENAI_API_KEY` once)
   - `MC_PRIVATE/docker/<service>.env` — service-specific overrides (optional)

   The generated `.env` is written to `~/.homelab/<service>/.env` (mode 600) and is
   gitignored. It's a regenerated artifact — `MC_PRIVATE` is the source of truth.

### Backups

The homelab Mac's backup script syncs `~/.homelab/*/data/` and `*/.env` from
remote servers into `MC_PRIVATE/backups/` via rsync over Tailscale SSH. A
launchd job runs daily. Since `MC_PRIVATE` lives on iCloud, backups are
automatically cloud-synced. See [machines/homelab/README.md](machines/homelab/README.md)
for restore steps.

## Docker Services

The `homelab` module (`config/homelab/`) deploys Docker Compose services
via Tailscale. See [config/homelab/README.md](config/homelab/README.md)
for architecture, env vars, and setup instructions.

## Development

```sh
cd ~/.machine

# build and run
uv sync --dev
uv run mc --help

# format, lint, test
./scripts/test.sh
```
