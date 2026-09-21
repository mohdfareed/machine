---
name: machine-context
description: Navigate this machine using mc to locate its configuration repository, relevant workspace paths, tools, and settings. Use when a task depends on machine-specific setup, when locating configuration ownership, or before machine setup and troubleshooting from another workspace.
---

# Machine Context

Use the machine configuration repository as a map, not proof of current state.
Start read-only and inspect only what the task needs. Ordinary project work does
not require a machine-wide audit.

## Locate the execution context

Establish the actual host, OS, shell, and workspace from available evidence.
Windows and WSL have different homes, executables, and configuration even when
sharing a saved machine ID. Local observations do not describe a remote host.

Agent subprocesses may skip interactive profiles. Prefer executable commands over
aliases or shell functions. Check relevant tools with `command -v` in Unix shells
or `Get-Command` in PowerShell; a missing command may be a PATH issue, not a
missing installation. Use installed tools' help rather than assuming flags.

Use these commands as needed:

- `mc show home`: locate the repository backing the installed CLI.
- `mc show id`: read the saved machine selection; blank means none is selected.
- `mc show status`: see the CLI version, selection, and repository location.

The saved selection is not proof of host identity. Status is not a health check.
If `mc` is unavailable, use the current workspace as locator
hints and verify the candidate repository. Do not assume a fixed checkout path,
scan the whole home directory, or install tools just to orient yourself. Report
missing access rather than inventing machine facts.

## Find relevant paths and configuration

Resolve repository paths below against the root returned by `mc show home`, not
against this skill's directory or the current workspace.

- `machines/<id>/machine.py` selects modules and machine-specific overrides.
- `machines/<id>/machine.env` contains committed values, including workspace or
  service paths when declared. Check only the values needed for the task.
- `config/` contains shared tool configuration and module declarations.
- `mc list` lists available machines and modules.
- `mc show` displays resolved packages, scripts, and file mappings without loading
  secrets. Check the saved selection first to avoid a prompt;
  use `mc show -m <id>` for an explicitly chosen machine.

These views resolve configuration for the current platform, not a remote host.
Use `mc --help` and command-specific help for options instead of guessing.

Trace installed settings back through file mappings and symlink targets before
editing. Use declared workspace paths when available, verify they exist, and
search only the relevant directory. Follow the destination project's instructions
once located; ordinary application code belongs there, not in this repository.

## Compare intent with live evidence

Verify relevant executable paths, versions, active configuration, or service
state. Declared packages and scripts do not prove installation or execution.

The CLI reads its saved selection from `~/.env`; inherited `MC_*` values can be
stale. Commands launched directly by an agent do not automatically receive the
selected-machine environment that `mc` prepares for deployment scripts. Do not
source arbitrary environment files to imitate that setup.

Never dump whole environments, private dotenv files, credentials, or keys. Use established
secret integrations without displaying values; do not load secrets for discovery.

## Follow the existing operational workflow

Before configuration changes or diagnosis, read the discovered repository's
`AGENTS.md` and relevant README notes. Load the appropriate repository skill:

- `.agents/skills/machine-configuration/SKILL.md` for setup and deployment.
- `.agents/skills/machine-diagnosis/SKILL.md` for review and troubleshooting.

These are repository-relative paths, not additional global skills. Shared setup
belongs in modules; host-specific setup belongs in machine declarations. Avoid
maintaining a second configuration beside the managed one.

Inspection is not permission to install, restart, sync, or deploy. `mc deploy`
changes files, installs missing packages, and runs scripts; `mc upgrade` performs
maintenance; `mc sync` changes the checkout and refreshes the installed CLI.
Do not run them merely to discover context. A request for repository edits is not
permission to deploy those edits.

Do not SSH to, deploy to, or otherwise mutate the homelab until the user has
reviewed repository changes and explicitly approved deployment.

Report repository intent, observed live state, proposed changes, and actions
actually performed separately. If access or validation is blocked, say so.
