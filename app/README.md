# Application architecture

## Follow a deployment

[cli/deploy.py](cli/deploy.py) is the recipe. It chooses a machine, calls
`build_env()` and `load_machine()`, then checks manager prerequisites. Only after
validation does it save the default selection and apply the resolved configuration:

```mermaid
flowchart LR
    Files[Link files] --> Managers[Prepare declared managers]
    Managers --> Init[Run init scripts]
    Init --> Packages[Install missing packages]
    Packages --> Scripts[Run setup scripts]
```

The CLI chooses script phases. Operations receive resolved inputs, the selected
environment, and execution options; they do not infer the workflow themselves.

## Where responsibilities belong

| Owner | Responsibility |
| --- | --- |
| [cli/](cli/) | Choose inputs, order work, and report outcomes. `entry.py` catches failures once. |
| [models.py](models.py) | Declaration shapes and field/type checks. |
| [machine.py](machine.py) + [discovery.py](discovery.py) | Find declarations; expand modules and dependencies; normalize paths and names; validate declarations; choose package sources. |
| [env.py](env.py) | Build selected-machine values, read host variables, resolve paths, and save/read the default selection. |
| [ops/](ops/) | Apply files, packages, and scripts; check live conditions and return results or raise. |
| [managers.py](managers.py) | Own package-manager commands, installation checks, bootstrap, and upgrades. |
| [shell.py](shell.py) + [scripts/](scripts/) | Prepare process environments and interpreters, execute commands, and handle command output. |
| [reporting.py](reporting.py) | Render application output through private Rich consoles. |

Business validation belongs in the loader, not model validators. The loader fixes
each package's source before execution; installed tools do not change that choice.
Derived `selected_source` is excluded from declaration constructors and schemas.

Only CLI modules and `shell.py` use reporting. All subprocesses go through
`shell.py`; lower layers never import the CLI or another module's private
implementation. [test_architecture.py](../tests/test_architecture.py) enforces these boundaries.

## How the environment reaches a command

`env.build_env(id)` builds explicit overrides in this order:

1. Base paths and identity derived from the selected machine.
2. Its committed `machine.env`.
3. `$MC_PRIVATE/machine.env`, preserving the resolved identity and base paths.

This does not read or change the saved selection. `~/.env` stores the default for
future invocations; `set_current_machine()` writes it separately. The same overrides
reach files, packages, and scripts. Only manager setup receives `MC_PKG_MANAGERS`.

Before each executable lookup or command, `shell.process_env()` reads the host
environment again. Unix activates installed commands through the internal
`environment.unix.sh`; Windows reads registered user/machine variables. Explicit
overrides win, and inherited Git repository/diff-tool context is removed.
The script runner honors each Unix shebang and adds `-f` for Zsh to skip user
startup files. PowerShell uses `-NoProfile` and receives the bundled `MachineAdmin`
module. Scripts inherit the prepared environment; explicitly launching another
shell with profiles can replace it.

Interactive Zsh activation belongs to Zim and `.zshrc`, independently of the app.
Normal Zsh startup loads saved and committed values and ordinary PATH settings
from `.zshenv`, without an app-specific guard.

## Other command flows

- [upgrade](cli/upgrade.py) upgrades declared managers and all their packages,
  then selected custom packages and `up_` scripts. Module filters limit custom
  maintenance, not manager-wide upgrades.
- [sync](cli/sync.py) fetches canonical main, merges with `--ff-only --autostash`,
  checks for restoration conflicts, then refreshes the CLI and completions.
- [show and list](cli/info.py) inspect configuration and selection without running
  setup or querying installed packages. Configuration inspection excludes secrets.

## Preview and failure behavior

`--dry-run` follows normal resolution and read-only checks, then skips mutations.
`query()` always performs its read; previewed `run()` calls only display the command.
Script internals are not simulated.

The first failure stops the workflow. Completed work is not rolled back. File
deployment preserves replaced real targets in adjacent backups and reports recovery
paths on failure. There is no script history or persistent application log;
deployment checks the actual files and installed packages each time.

Validate changes with `./scripts/check.sh`. Regression tests cover environment
precedence, validation before mutation, previews, data preservation, and failures.
