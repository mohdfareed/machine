# Machine Configuration & Setup

Cross-platform machine setup and management. Shared modules define packages,
dotfiles, and setup scripts; per-machine manifests select the desired modules
and any per-machine configuration/overrides.

The `mc` CLI deploys a machine, upgrades it, syncs with canonical `main`, and
inspects the resolved configuration.

The [homelab](config/homelab/README.md) configuration extends it to
self-hosted services. It manages Docker-based servers setup, configuration,
and service deployment.

## Requirements

- Python 3.8 or higher
- [App Installer](https://learn.microsoft.com/en-us/windows/package-manager/winget/) (Windows)
- Apt (Linux)

## Bootstrap

Install the repository and CLI:

```sh
# unix
repo="https://raw.githubusercontent.com/mohdfareed/machine/main"
curl -LsSf $repo/scripts/bootstrap.sh | sh -s -- --deploy
```

```powershell
# powershell
$repo = "https://raw.githubusercontent.com/mohdfareed/machine/main"
$script = irm $repo/scripts/bootstrap.ps1
& ([scriptblock]::Create($script)) -Deploy
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
cd (mc show home)
wsl -- sh ./scripts/bootstrap.sh --deploy
```

## Usage

```sh
mc deploy [mods...]  # Deploy all or the selected modules to the machine
mc upgrade           # Upgrade installed packages and run upgrade scripts
mc sync              # Integrate canonical main and refresh the CLI
mc show              # Inspect resolved configuration
```

`mc deploy -n` previews deployment without making changes. `-n`/`--dry-run` also
applies to `upgrade` and `sync`. Add `--debug` to show exception tracebacks.

### Machines

Create `machines/<id>/machine.py`:

```python
from app.models import Machine
from config.terminal import shell

manifest = Machine(
    modules=[shell],
)
```

> **NOTE:** A Windows machine's manifest is also used during the WSL deployment.
> Ensure the manifest configures WSL using the appropriate platform flags.

Replace `<id>` below with the machine name:

```sh
mc show -m <id>    # Inspect the resolved manifest
mc deploy -m <id>  # Set machine selection and deploy
```

Homebrew on Unix, WinGet on Windows, and APT on Linux/WSL are prerequisites;
they are auto-installed when possible.

#### Environment

Declare public environment variables in the manifest's `env` mapping, using
strings or `Path` values. Redeploy after changing these variables, then open a new terminal.

### Modules

Create `config/<name>/module.py` and an empty `__init__.py` beside it:

```python
from app.models import Module

module = Module()
```

To deploy a specific module, import its folder into the manifest's `modules`
list, then `mc deploy <name>` to set up that module on the selected machine.

CLI arguments use dotted names:
`config/terminal/git/module.py` becomes `terminal.git`.
Discovery recursively finds the reserved `module.py` filename, **folder names
must be valid Python identifiers, not keywords.**

With `from config import terminal`, `modules=[terminal]` includes all modules
under that grouping folder, including newly added ones. Grouping folders also
need an empty `__init__.py`. **Import folders, not their `module.py` files.**

### Scripts

Create scripts directly in `config/<name>/scripts/` or `machines/<id>/scripts/`.
Top-level `.sh`, `.py`, and `.ps1` files are auto-discovered.

`.sh` scripts run only on Unix, never on Windows. Untagged `.py` and `.ps1`
scripts run on all platforms. Tags narrow that selection, e.g. `setup.mac.sh`:

| Tag      | Runs on           |
| -------- | ----------------- |
| `.mac`   | macOS             |
| `.linux` | Linux, WSL        |
| `.unix`  | macOS, Linux, WSL |
| `.win`   | Windows           |
| `.wsl`   | WSL               |

| Prefix  | When it runs                     |
| ------- | -------------------------------- |
| `init_` | Before dotfiles and packages     |
| `up_`   | Only during `mc upgrade`         |
| `_`     | Helper; never auto-executed      |
| None    | Every deployment, after packages |

### Secrets

On machines selecting `onepass`, sign in and enable **SSH Agent**, **Generate
SSH config files with bookmarked hosts**, and **Developer Integrations** in
Developer settings. On an existing Windows installation, stop and disable
Windows' `ssh-agent` service if enabled.

Sign in to Tailscale to SSH into connected machines using keys stored in 1Password.

## Development

```sh
uv sync --dev                    # Install dev dependencies
uv run mc --help                 # Run dev CLI without installing
uv run mc validate [-m MACHINE]  # Validate machine configuration and modules
./scripts/fix.sh                 # Upgrade dependencies, auto-fix, and validate
./scripts/check.sh               # Validate codebase without modifying files
./scripts/bootstrap.sh           # Install the dev build (symlinked)
```
