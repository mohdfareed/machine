# Machine Configuration & Setup

Cross-platform machine setup and management. Shared modules define tools,
dotfiles, and setup scripts; per-machine manifests selects what a machine needs,
with machine-specific configuration and overrides.

The `mc` CLI deploys configuration, installs missing packages, runs maintenance,
and syncs repository changes across machines.

The [homelab](config/homelab/README.md) configuration extends this to
self-hosted services. It manages a Docker-based server setup and configuration
and service deployment.

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

`mc show` lists configured files, packages, and scripts for the platform.
`mc deploy -n` previews deployment without making changes. `-n`/`--dry-run`
also applies to `upgrade` and `sync`.
Add `--debug` to show exception tracebacks.

### Machines

Create `machines/<id>/machine.py`:

```python
from app.models import Machine, PkgManager
from config.terminal import shell

manifest = Machine(
    pkg_managers=[PkgManager.BREW],
    modules=[shell],
)
```

> **NOTE:** A Windows machine's manifest is also used during the WSL deployment.
> Ensure the manifest configures WSL using the appropriate platform flags.

The deployed machine is stored in `MC_ID` at `~/.env`; the CLI and shell
startup use that file. Scripts launched by `mc` preserve the environment
prepared for their selected machine.

Use `mc list` to find modules to import.
Replace `<id>` below with the machine name:

```sh
mc show -m <id>    # Inspect the resolved manifest
mc deploy -m <id>  # Select, remember, and deploy it
```

### Modules

Create `config/<name>/module.py` and an empty `__init__.py` beside it:

```python
from app.models import Module

module = Module()
```

Import its folder into the manifest's `modules` list, then `mc deploy <name>` to
set up that module on the selected machine. CLI arguments use dotted names:
`config/terminal/git/module.py` becomes `terminal.git`.
Discovery descends through grouping folders and stops at each `module.py`;
**folder names must be valid Python identifiers.**

With `from config import terminal`, `modules=[terminal]` includes all modules under
that grouping folder, including newly added ones. Grouping folders also need an
empty `__init__.py`. Import folders, not their `module.py` files.
Files and scripts declared in the modules remain relative to their module folder.

### Scripts

Drop scripts directly in `config/<name>/scripts/` or `machines/<id>/scripts/`.
Top-level `.sh`, `.py`, and `.ps1` files are auto-discovered.
Use explicit `scripts=` only for files outside those directories.

Platform tags go before the extension, e.g. `setup.unix.sh`.
No tag means all platforms, so tag shell-specific scripts.

| Tag      | Runs on           |
| -------- | ----------------- |
| `.mac`   | macOS             |
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

The first failed operation stops deployment or upgrade.
Before each command, `mc` prepares current host variables and tool activation,
then applies the selected machine's variables and secrets.
Declare machine-specific values in `machine.env`; environment refresh is
handled internally by the app.

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
./scripts/fix.sh        # Upgrade dependencies, auto-fix, and validate
./scripts/check.sh      # Validate without changing files
./scripts/bootstrap.sh  # Install the dev build (symlinked)
```

### Agent workflows

Use `machine-configuration` for creating configs and deploying changes, or
`machine-diagnosis` for reviewing the setup and troubleshooting a machine.
Specify the target machine and whether you want inspection, repo changes, or deployment.
