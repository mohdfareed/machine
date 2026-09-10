# Machine Configuration & Setup

Cross-platform machine setup and management. Shared modules define tools,
dotfiles, and setup scripts; per-machine manifests selects what a machine needs,
with machine-specific configuration and overrides.

The `mc` CLI deploys configuration, installs missing packages, runs maintenance, and syncs repository changes across machines.

The [homelab](config/homelab/README.md) configuration extends this to self-hosted services.
It manages a Docker-based server setup and configuration and service deployment../

## Bootstrap

Run the following to bootstrap and deploy a new machine:

```sh
# unix
repo="https://raw.githubusercontent.com/mohdfareed/machine/main"
curl -LsSf $repo/scripts/bootstrap.sh | sh
~/.local/bin/mc --help  # added to PATH on deploy
```

```powershell
# powershell
$repo = "https://raw.githubusercontent.com/mohdfareed/machine/main"
irm $repo/scripts/bootstrap.ps1 | iex
~/.local/bin/mc --help  # added to PATH on deploy
```

By default, the repo is deployed to `~/.machine`. Export `MC_HOME` before
deployment to change it. To re-deploy at a different path and reinstall `mc`:

1. After moving the checkout,
2. set `MC_HOME` to its new path, and
3. rerun `./scripts/bootstrap.sh` (or `./scripts/bootstrap.ps1`).

### WSL

To set up WSL, run the following after a Windows machine is deployed:

```powershell
cd $env:MC_HOME
wsl -- bash ./scripts/bootstrap.sh
wsl -- bash -c '$HOME/.local/bin/mc --help'
```

## Usage

```sh
mc deploy            # Deploy the selected machine
mc deploy shell git  # Only these modules; skip machine-level extras
mc update            # Run up_* scripts and rerun script-backed packages
mc sync              # Fetch canonical main, fast-forward if possible, then deploy
mc sync --no-deploy  # Sync without deploying
mc status            # Current machine and local paths
mc show              # List files, packages, and scripts in deployment order
```

`mc sync` fetches canonical `main`, fast-forwards with autostash, then deploys.
Local edits are preserved. Conflicts stop before deployment; use Git to resolve them.
Merge work-fork changes into canonical `main` on your personal machine.
Preserve commits with a regular merge so the work branch can fast-forward afterward.

### Machines

Create `machines/<id>/manifest.py`:

```python
from app.models import Machine, PkgManager

manifest = Machine(
    pkg_managers=[PkgManager.BREW],
    modules=["shell"],
)
```

> **NOTE:** A Windows machine's manifest is also used during the WSL deployment.
> Ensure the manifest configures WSL using the appropriate platform flags.

The `core` module is always included, including module-filtered runs, and owns
shared setup such as package-manager installation and maintenance.
Declare each machine's managers in `pkg_managers`; an empty list enables none.

Use `mc list` to find module names to add. Replace `<id>` below with the directory name:

```sh
mc show -m <id>    # Inspect the resolved manifest
mc deploy -m <id>  # Select, remember, and deploy it
```

### Modules

Create `config/<name>/module.py`:

```python
from app.models import Module

module = Module()
```

Add its name to the manifest's `modules` list, then `mc deploy <name>` for just that
module on the selected machine. Nested modules use dotted names:
`config/tools/tool/module.py` becomes `tools.tool`, including in `depends`.
Discovery descends through grouping folders and stops at each `module.py`;
**folder names cannot contain dots.**
Files and scripts remain relative to their module folder.

In manifests, `modules=["tools"]` includes all modules under that grouping folder,
including newly added ones. CLI filters and `depends` still use exact module names.

### Scripts

Drop scripts directly in `config/<name>/scripts/` or `machines/<id>/scripts/`.
Top-level `.sh`, `.py`, and `.ps1` files are auto-discovered; no list needed.
Use explicit `scripts=` only for files outside those directories.

Platform tags go before the extension, e.g. `watch_setup.unix.sh`.
No tag means all platforms, so tag shell-specific scripts.

| Tag      | Runs on           |
| -------- | ----------------- |
| `.macos` | macOS             |
| `.linux` | Linux, WSL        |
| `.unix`  | macOS, Linux, WSL |
| `.win`   | Windows           |
| `.wsl`   | WSL               |

| Prefix   | When it runs                                                 |
| -------- | ------------------------------------------------------------ |
| `init_`  | During deployment, after files and before packages           |
| `once_`  | Once, then skipped while recorded in local state             |
| `watch_` | First deployment, then when the script's own content changes |
| `up_`    | Only during `mc update`                                      |
| `_`      | Helper; never auto-executed                                  |
| None     | Every deployment, after packages                             |

Configuration validation errors or a failed `init_` script stop the entire deployment.
Unhandled errors also stop the run. Dependencies control ordering, not failure isolation.
Before execution, `mc` prepares each script's environment: shared variables such
as `MC_HOME` and `MC_ID`, machine config and secrets, then shell-specific additions.

### Secrets

Keep secrets out of Git: `$MC_PRIVATE/env/$MC_ID.env`, plain `KEY=VALUE`.
Set `MC_PRIVATE` in `machines/<id>/machine.env` to my private storage;
otherwise it defaults to the app data directory's `private/`.
Don't put secrets in `machine.env` or the generated `~/.env`.

```sh
mc private  # Resolve the selected machine's private directory
secrets     # Load private env into this shell (shell module helper)
```

`mc` already loads the private env for scripts; don't source it again there.

## Development

From the repo:

```sh
uv sync --dev           # Install dev dependencies
uv run mc --help        # Run dev CLI without installing
./scripts/fix.sh        # Format and auto-fix problems
./scripts/check.sh      # Validate before committing
./scripts/bootstrap.sh  # Install the dev build (symlinked)
```

### Agent workflows

Use `machine-configuration` for creating configs and deploying changes, or
`machine-diagnosis` for reviewing the setup and troubleshooting a machine.
Specify the target machine and whether you want inspection, repo changes, or deployment.
