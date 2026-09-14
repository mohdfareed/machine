# Machine Configuration & Setup

Cross-platform machine setup and management. Shared modules define tools,
dotfiles, and setup scripts; per-machine manifests selects what a machine needs,
with machine-specific configuration and overrides.

The `mc` CLI deploys configuration, installs missing packages, runs maintenance,
and syncs repository changes across machines.

The [homelab](config/homelab/README.md) configuration extends this to self-hosted services.
It manages a Docker-based server setup and configuration and service deployment.

## Bootstrap

Run the following to install the repository and CLI on a new machine:

```sh
# unix
repo="https://raw.githubusercontent.com/mohdfareed/machine/main"
curl -LsSf $repo/scripts/bootstrap.sh | sh -s -- --deploy
```

```powershell
# powershell
$repo = "https://raw.githubusercontent.com/mohdfareed/machine/main"
$script = irm $repo/scripts/bootstrap.ps1
& ([scriptblock]::Create($script) -Deploy
```

Restart the shell afterward to make `mc` available on `PATH`.

By default, the repo is deployed to `~/.machine`. Export `MC_HOME` before
bootstrapping to change it. To re-deploy at a different path and reinstall `mc`:

1. After moving the checkout,
2. set `MC_HOME` to its new path, and
3. rerun `./scripts/bootstrap.sh` (or `./scripts/bootstrap.ps1`).

### WSL

To set up WSL, run the following after a Windows machine is deployed:

```powershell
cd $env:MC_HOME
wsl -- bash ./scripts/bootstrap.sh --deploy
```

## Usage

```sh
mc deploy [mods...]  # Deploy all or the selected modules to the machine
mc upgrade           # Upgrade installed packages and run upgrade scripts
mc sync              # Integrate canonical main and refresh the CLI
mc show              # Inspect resolved configuration
```

`mc sync` is used to sync the deployment with canonical `main`. It fetches
`main`, fast-forwards with autostash, and refreshes the installed CLI and shell
completion. Local edits are preserved. Conflicts stop the sync; use Git to
resolve them manually then re-run.

### Machines

Create `machines/<id>/machine.py`:

```python
from app.models import Machine, PkgManager

manifest = Machine(
    pkg_managers=[PkgManager.BREW],
    modules=["terminal.shell"],
)
```

> **NOTE:** A Windows machine's manifest is also used during the WSL deployment.
> Ensure the manifest configures WSL using the appropriate platform flags.

The default machine is `MC_ID` in `~/.env`; the CLI and shell startup use that file.
Scripts launched by `mc` preserve the environment prepared for their selected machine.
With no saved selection, deployment prompts for a machine.
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

Add its name to the manifest's `modules` list, then `mc deploy <name>` for just
that module on the selected machine. Nested modules use dotted names:
`config/terminal/git/module.py` becomes `terminal.git`, including in `depends`.
Discovery descends through grouping folders and stops at each `module.py`;
**folder names cannot contain dots.**
Files and scripts remain relative to their module folder.
In manifests, `modules=["terminal"]` includes all modules under that grouping folder,
including newly added ones. CLI filters and `depends` still use exact module names.

### Scripts

Drop scripts directly in `config/<name>/scripts/` or `machines/<id>/scripts/`.
Top-level `.sh`, `.py`, and `.ps1` files are auto-discovered; no list needed.
Use explicit `scripts=` only for files outside those directories.

Platform tags go before the extension, e.g. `setup.unix.sh`.
No tag means all platforms, so tag shell-specific scripts.

| Tag      | Runs on           |
| -------- | ----------------- |
| `.macos` | macOS             |
| `.linux` | Linux, WSL        |
| `.unix`  | macOS, Linux, WSL |
| `.win`   | Windows           |
| `.wsl`   | WSL               |

| Prefix  | When it runs                                       |
| ------- | -------------------------------------------------- |
| `init_` | During deployment, after files and before packages |
| `up_`   | Only during `mc upgrade`                           |
| `_`     | Helper; never auto-executed                        |
| None    | Every deployment, after packages                   |

Scripts check existing setup themselves; there is no saved run history.
The first failed operation stops deployment or upgrade. Fix the reported error,
then rerun. Dependencies control ordering, not failure isolation.
Before each command, `mc` prepares current host variables and tool activation,
then applies the selected machine's variables and secrets. Declare machine-specific
values in `machine.env`; environment refresh is handled internally by the app.

`mc show` lists configured files, packages, and scripts for the current platform.
`mc deploy -n` previews operations against the current setup. `-n`/`--dry-run`
also applies to `upgrade` and `sync`. Commands use the
terminal directly. Add `--debug` to show exception tracebacks;
the CLI does not write log files.

### Secrets

Set `MC_PRIVATE` in `machines/<id>/machine.env` to my private storage;
it defaults to `<repository>/private`. Keep secret values out of
committed machine files and the generated `~/.env`.

The app, Zsh `mc::secrets`, and PowerShell `Import-Secrets` read
`$MC_PRIVATE/machine.env`, plain `KEY=VALUE`.

```sh
mc show private  # Resolve the selected machine's private directory
mc::secrets      # Load private env into this shell (shell module helper)
```

`mc` already loads its private env file for scripts; don't source it again there.

## Development

Application responsibilities and enforced boundaries are in [app/README.md](app/README.md).

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
