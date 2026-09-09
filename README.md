# Machine notes

## Bootstrap

macOS / Linux / WSL:

```sh
curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/scripts/bootstrap.sh | sh
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/mohdfareed/machine/main/scripts/bootstrap.ps1 | iex
```

Default checkout: `~/.machine`. Export `MC_HOME` first for a different path
(`$env:MC_HOME` in PowerShell).

To re-deploy at a different path and reinstall `mc`:

1. After moving the checkout,
2. set `MC_HOME` to its new path, and
3. rerun `./scripts/bootstrap.sh` (or `./scripts/bootstrap.ps1`).

## Usage

```sh
mc apply             # Apply the selected machine
mc apply shell git   # Only these modules; skip machine-level extras
mc update            # Run up_* scripts and rerun script-backed packages
mc sync              # Pull --rebase, then apply the selected machine
mc sync --push       # Also push local commits
mc sync --no-apply   # Pull without applying
mc status            # Current machine and local paths
mc show              # List files, packages, and scripts in apply order
```

### Machines

Create `machines/<id>/manifest.py`:

```python
from machine.manifest import MachineManifest, PkgManager

manifest = MachineManifest(
    pkg_managers=[PkgManager.BREW],
    modules=[],
)
```

`core` is always included, including module-filtered runs, and owns shared setup
such as package-manager installation and maintenance.
Declare each machine's managers in `pkg_managers`; an empty list enables none.

Use `mc list` to find module names to add. Replace `<id>` below with the directory name:

```sh
mc show -m <id>       # Inspect the resolved manifest
mc apply -m <id>      # Select, remember, and apply it
```

### Modules

Create `config/<name>/module.py`:

```python
from machine.manifest import Module

module = Module()
```

Add its name to the manifest's `modules` list, then `mc apply <name>` for just that
module on the selected machine. Nested modules use dotted names:
`config/tools/tool/module.py` becomes `tools.tool`, including in `depends`.
Discovery descends through grouping folders and stops at each `module.py`;
**folder names cannot contain dots.**
Files and scripts remain relative to their module folder.

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

| Prefix   | When it runs                                            |
| -------- | ------------------------------------------------------- |
| `init_`  | During apply, after files and before packages           |
| `once_`  | Once, then skipped while recorded in local state        |
| `watch_` | First apply, then when the script's own content changes |
| `up_`    | Only during `mc update`                                 |
| `_`      | Helper; never auto-executed                             |
| None     | Every apply, after packages                             |

Configuration validation errors or a failed `init_` script stop the entire apply.
Unhandled errors also stop the run. Dependencies control ordering, not failure isolation.
Before execution, `mc` prepares each script's environment: shared variables such
as `MC_HOME` and `MC_ID`, machine config and secrets, then shell-specific additions.

### Secrets

Keep secrets out of Git: `$MC_PRIVATE/env/$MC_ID.env`, plain `KEY=VALUE`.
Set `MC_PRIVATE` in `machines/<id>/machine.env` to my private storage;
otherwise it defaults to the app data directory's `private/`.
Don't put secrets in `machine.env` or the generated `~/.env`.

```sh
mc private           # Resolve the selected machine's private directory
secrets              # Load private env into this shell (shell module helper)
```

`mc` already loads the private env for scripts; don't source it again there.

## Development

From the checkout:

```sh
uv sync --dev         # Install dev dependencies
uv run mc --help      # Run dev CLI without installing
./scripts/fix.sh      # Format and auto-fix problems
./scripts/check.sh    # Validate before committing
```

## Related notes

- [Homelab deployment](config/homelab/README.md)
- [Homelab machine](machines/homelab/README.md)
- [Media stack](machines/homelab/docker/media/README.md)
- [Raycast](config/raycast/README.md)
