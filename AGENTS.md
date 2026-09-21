# Dev Machine (`mc`)

Cross-platform machine bootstrap tool and dotfile manager.

This repository is also the operating context for managing machines. For operational
work, identify the target host and compare relevant repository configuration with
live state; manifests describe intent, not proof of deployment. Use the two skills
under `.agents/skills/`: `machine-configuration` for setup and deployment, and
`machine-diagnosis` for reviews and troubleshooting. Inspect only relevant data;
never expose credentials or secret values in output.

> **Agent instruction:** This file contains project-specific conventions,
> constraints, and preferences that shape how you work on this codebase.
> When the user states a preference or rule ("never do X", "always use Y"),
> add it here. When the project changes in a way that contradicts an existing
> note, update or remove it. Do this proactively - don't wait to be asked.
>
> Use Codex memories for cross-session context. This file is for durable coding
> standards, not session notes. Keep repo-specific Codex skills under
> `.agents/skills/`; keep portable tool configuration with its module and
> mutable runtime state machine-local.
>
> ALWAYS ensure README.md and AGENTS.md are consistent and up-to-date with the
> latest project conventions and rules.

## Tech Stack

- **Language**: Python 3.14+
- **CLI**: Typer + Rich
- **Config**: Pydantic models, Python manifests
- **Packaging**: uv (build, lock, tool install)
- **Linting**: Ruff (line-length 100, rules: E, I, W, RUF)
- **Type checking**: Pyright (standard mode)

## Project Layout

- `app/cli/` - CLI entrypoint, separate deploy/upgrade/sync commands, info commands, and shared reporting
- `app/models.py` - Configuration data shapes and field/type checks
- `app/reporting.py` - Shared Rich consoles and small human-facing presentation helpers
- `app/discovery.py` - Machine, module, and script discovery
- `app/machine.py` - `load_machine()` resolves declarations into one combined `Machine`
- `app/env.py` - Host facts, explicit selected-machine environment, and saved selection
- `app/shell.py` - Explicit command execution/preview, bounded queries, and fresh execution environments
- `app/managers.py` - Package-manager setup, presence checks, installation, and maintenance
- `app/ops/` - File, package, and script deployment
- `app/scripts/` - Internal command activation and PowerShell module root
- `config/` - Shared dotfiles and configs
- `machines/` - Per-host configurations
- `scripts/bootstrap.sh` / `scripts/bootstrap.ps1` - Bare-machine bootstrap

## Commands

- `./scripts/check.sh` (Windows: `./scripts/check.ps1`) - Non-mutating native validation entrypoint (always use this to validate)
- `./scripts/fix.sh` (Windows: `./scripts/fix.ps1`) - Complete pre-commit preparation: upgrade and sync dependencies, fix unambiguous spelling without renaming files, format, auto-fix lint, and normalize Unix script permissions before re-running checks
- `uv run mc --help` - Run CLI in dev
- `--dry-run`/`-n` belongs only to `deploy`, `upgrade` and `sync`, after the command name.
  Information commands live under `show` (`id`, `home`, `status`);
  bare `show` inspects resolved configuration and `list` stays at the root.
- `mc sync` fetches canonical `mohdfareed/machine` main, integrates with Git's
  fast-forward-only merge with autostash, then refreshes the installed CLI and shell
  completion. Tracked
  local edits are restored before the refresh; ahead commits and detached HEAD are
  allowed. Git failures or autostash restoration conflicts stop the sync. Never
  discard local changes; leave conflicting auto-stashes for recovery with Git.
  Branches, commits, pushes, and PRs belong to Git.

## Architecture

Use [app/README.md](app/README.md) to trace complete application flows and review
responsibility changes before implementing them. Keep the current architecture,
proposed design and enforced rules distinct; isolated fixes do not replace this review.
Models perform field/type checks only. The loader explicitly normalizes and validates
declarations; operations check live prerequisites. Keep loader-derived bookkeeping
out of declaration constructors and schemas. Pass execution options and the
selected environment explicitly. Keep the complete Typer command tree in
`app/cli/entry.py`; command modules implement callbacks only. Only CLI modules and
`app/shell.py` import reporting; other layers return facts or raise. Keep these boundaries
enforced by the existing tests.

### Module (`config/<path>/module.py`)

Module names are dotted paths relative to `config/`: `terminal/git/module.py`
is `terminal.git`. Discovery recurses through grouping folders, stopping at
module directories; folder names must be valid Python identifiers, not keywords. `FileMapping` accepts strings
or `Path` values and stores paths internally. Script lists use `Path`; sources
and scripts resolve relative to the module directory.
The loader expands target variables and `~`, not model construction.
Module code must locate bundled resources relative to its own files, never by
reconstructing its `config/...` location from `MC_HOME` or the working directory.

Exports a `Module(files, packages, scripts, depends)`. `depends` and manifest
`modules` contain imported config folders (`list[ModuleType]`), including groups.
Use grouped folder imports such as `from config.terminal import git, shell`.
Keep an empty `__init__.py` in `config/` and each module/group folder so Python and
editors recognize them as packages. Keep these markers empty; declarations stay
in `module.py` and are loaded by the app.
Scripts under `scripts/` are auto-discovered; explicit `scripts=` list
is only needed for files outside that directory. `depends=[other]`
auto-includes prerequisite modules in manifests (deduped, ordered before
the dependent).

`terminal.ssh.client` and `terminal.ssh.server` share the `terminal.ssh` group;
the server depends on the client. Machines select `terminal.ssh` for both or
`terminal.ssh.client` alone. Python runtimes belong to the separately selected
`development.python` module; bootstrap supplies uv through Homebrew on Unix and
WinGet on Windows. Homebrew is a Unix bootstrap prerequisite.

The optional `onepass` module owns its desktop app, CLI, SSH integration, and Git
signing. Ordinary SSH and Git must work without selecting it; Gleason's IT policy
prohibits 1Password. Deployment must not
copy private keys or load them into another agent. Track the shared public-key
allowlist in the SSH server module and deploy it through `FileMapping`. Scripts
that need credentials may authenticate through the CLI; do not automate account enrollment.

### Manifest (`machines/<id>/machine.py`)

Exports a `Machine(pkg_managers, modules, files, packages, scripts)`.
Composes imported modules and adds machine-specific overrides. The loader derives
full names from folder references; CLI filters use dotted strings. Both select the
module or its dotted descendants: `terminal` matches `terminal` and `terminal.*`,
not `terminal_extra`. Expansion uses discovery
order, then existing dependency ordering and deduplication; no matches is an error.
`load_machine(machine_id, module_names=None, *, env)` returns a `Configuration` with
full module names and applicable, normalized files/packages/scripts with fixed package
sources. Declaration files execute afresh on each load; cached folder imports carry
no resolved state. Filters include selected modules
and their prerequisites and related overrides, excluding unrelated machine extras.
Package managers remain machine-wide: the loader adds platform prerequisites to
the optional declarations. Installed-tool availability never changes source selection.

### Cross-Platform Requirements

- Always verify Windows compatibility when touching files, paths, or scripts
- Use `Platform.is_a()` for platform-family matching: WSL matches Linux and Unix; macOS and Linux match Unix. Keep these relationships in the enum.
- Windows SSH client is OpenSSH (built into Windows 10+): supports `~`, `IgnoreUnknown`
- Unix shell files and ShellCheck configuration use LF line endings
- Shell scripts need platform tags (`.unix.sh` / `.win.ps1`) - never assume Unix-only
- Path separators: use `pathlib.Path` in Python; avoid hardcoded `/` in target strings

### Packages and Files

- Machines include only declared modules and their dependencies. OS settings and features belong in the explicitly selected `system` module. Platform managers are fixed prerequisites: Homebrew on macOS, WinGet on Windows, and APT plus Homebrew on Linux/WSL. Manifests declare only optional MAS, Scoop, or Snap in `pkg_managers`; never infer managers from packages or PATH. Bootstrap supplies Homebrew and uv on Unix; WinGet supplies uv on Windows. `BREW` includes casks. The loader validates optional manager compatibility, and `app/managers.py` installs missing optional managers directly. Installation and maintenance use the complete resolved manager list; custom scripts follow the same policy.

- Define packages with `Package(...)` directly; package helper constructors (`brew(...)`, `apt(...)`, etc.) are removed
- `FileMapping(mode=...)` owns mapped-file permissions; owner-only modes use a current-user and SYSTEM ACL on Windows
- Use `FileMapping(platforms=...)` for intentionally platform-specific files instead of conditionally constructing file lists
- Use `cask=` for Homebrew casks; package source selection is platform-aware and should replace package-level `if PLATFORM ...` conditionals in manifests/modules
- Use package `platforms=` only when a package is intentionally restricted or command-backed; normal multi-manager package selection should not need manifest-level platform conditionals
- `mc deploy` only installs missing packages; upgrades belong to `mc upgrade`. Report skipped packages as already installed using dim CLI output. If a package exists but is not managed by the requested manager, `mc deploy` should still install it with that manager
- Package dry runs skip installed-package and custom-command presence checks so
  every selected installation is reported, even when already installed.
- Command-backed packages use `Package.name` as the installed-command check during `mc deploy`; `mc upgrade` runs `up_cmd`, reuses `cmd` when `up_cmd=True`, or lists the package for manual maintenance. Manager sources take precedence over custom commands on platforms where they apply
- Bundled installers belong in ordinary setup and `up_` scripts, not shell-quoted script paths inside package declarations.

### Script Pipeline and Environment

- Platform tags on scripts: `name.mac.sh`, `name.unix.sh`, `name.win.ps1`
- Script prefixes: `init_` = prepare host settings and package prerequisites before files and packages, `up_` = run only during `mc upgrade`, `_` = helper (never auto-executed, sourced by other scripts)
- Execution order: optional manager setup → `init_*` scripts → files → packages → remaining scripts
- `~/.env` stores `MC_ID`. `mc deploy` writes it; the CLI reads the selected machine directly from this file, not the inherited shell environment or a separate state file. The app derives its root from its code; `MC_HOME` is only a bootstrap destination option.
- `app.env.build_env` combines the selected machine's base variables with its committed `machine.env`; the selected identity and machine path take precedence. Scripts inherit these public values and do not re-source them.
- Secrets belong to 1Password and the consuming application. The app does not load private dotenv files or manage private SSH keys. Compose projects commit reference-only `secrets.env` files; the homelab script uses `op run --env-file=secrets.env` on every platform. Homepage (dashboard) stays on the homelab machine and consumes its mounted Tailscale Environment through Compose. Prefer vault, item, and field IDs so renaming them does not break references. Keep secret values out of Python and the general deployment environment.
- Shell profiles load `~/.env` and the selected machine's committed `machine.env` through the `~/.env.mc` symlink. Shell-specific extras use `.zshenv.mc`, `.zshrc.mc`, and profile-relative `profile.mc.ps1` links. The script runner honors Unix shebangs and starts Zsh with `-f` to skip user startup files; scripts inherit the app's prepared environment.
- Zim owns interactive Zsh plugins, Homebrew activation, and completion initialization. Declare plugins in `config/terminal/shell/zsh/.zimrc`; install and update them through the `terminal.shell` module's deployment and upgrade scripts. Shell configuration must not source application helpers.
- Windows SSH uses the same PowerShell 7 and profile as local terminals. Elevate
  system changes through `Invoke-Admin`; do not require the whole deployment to
  run as Administrator or add recurring link-repair scripts. Scoop owns PowerShell
  installation and upgrades; configure `no_junction` before packages install and
  register its stable executable launcher as the SSH login shell.
- `machine.env` uses plain `KEY=VALUE` (no `export`); values may reference earlier vars
- Scripts check their own prerequisites and existing setup before changing anything; there is no script-run history. Package presence is determined from the requested package manager at deployment time.

`build_env(machine_id)` prepares explicit machine overrides without reading the saved
selection. Every executable lookup and command prepares the current host environment,
then applies those overrides. Subprocess environments exclude Git repository and
diff-tool context from the caller; global Git configuration and authentication remain
available. Internal Unix activation lives in `app/scripts/environment.sh`;
it must be quiet, read-only, safe before tools are installed, and safe to source repeatedly.
Windows reads registered machine/user variables without loading PowerShell profiles.
Shell execution prepares the chosen
PowerShell interpreter with `-NoProfile`, `-File`, and the bundled
`MachineAdmin` module under `app/scripts/` while preserving existing module paths,
immediately before real use. PowerShell modules use the standard `<Name>/<Name>.psm1`
layout beneath this module root.
Elevation is explicit through `Invoke-Admin { ... }`; pass outside values using
`param(...)` and `-ArgumentList` because elevated blocks run in a separate process. Elevated text output and errors
are relayed to the caller for terminal display.

### Configuration Ownership and State

Give configuration one owner: shared setup belongs in modules, host-specific setup
belongs in machine manifests. Commit portable configuration; keep credentials,
runtime state, caches, and machine-generated application data local.
Keep `config/` organized as the catalog of selectable modules and module groups;
`machines/` composes those declarations. Routine configuration changes belong there.
Group tools by their function, not properties such as having a graphical interface.
Keep standalone tools at the root; grouping folders should contain multiple related
tools, not wrap a single tool just to categorize every root entry.
Execution, environment refresh, and bootstrap orchestration belong in `app/`,
including their supporting scripts. Do not move application internals into `config/`
or add special config entrypoints outside the module declaration system.

- Machine extras: `extra.zsh` → `~/.zshrc.local`
- Repo root is `app.env.ROOT`, derived from the installed code location; execution never reads a mutable root setting
- The CLI keeps no separate selection file or log files. Invocation options belong to the CLI context; command metadata comes from the package entry point, outside configuration models.
- Workspace-local editor config lives in `.vscode/` for VS Code and `.zed/` for Zed only for repo-specific file associations and context servers; personal editor defaults belong in `config/development/vscode/` and `config/development/zed/`
- VS Code Remote Tunnels are owned by the `development.vscode` module; account authorization remains a one-time manual step on each machine
- The `development.agents` module installs Codex; credentials, pairing/enrollments, live databases, histories, caches, downloaded plugins, and generated memories stay machine-local
- Editor tasks should avoid ad hoc external tool dependencies; prefer shell builtins or repo-managed entrypoints so tasks stay portable across machines
- Shared repo policy should prefer cross-editor files (`pyproject.toml`, `.editorconfig`, `.shellcheckrc`, `.markdownlint.json`) over editor-specific settings
- Standalone services own their code, tests, dependencies, documentation, and internal directory setup; this repo owns only deployment wiring and host prerequisites

## Coding Conventions

- Before writing new code, check the codebase for existing patterns and follow them
- Minimize lifetime maintenance: count code ownership, repeated configuration, dependencies, and manual recovery as well as line count. Prefer established mechanisms and fewer general-purpose tools over specialized tools for minor conveniences. Keep ordinary package additions as configuration changes. Write direct, readable steps and preserve the established comment and section structure.
- Keep runtime references rename-safe: use symbol references or framework metadata instead of duplicating internal names in strings, and explicit attributes for package access. Keep external contracts literal; do not add a naming framework. Tests are exempt.
- Always keep the happy path flat: handle alternative, skip, and failure paths first with early `return`, `continue`, `break`, or exceptions as appropriate, then let the main path proceed without unnecessary nesting or `else`. Apply this throughout control flow, not just validation; preserve required cleanup and shared follow-up work.
- Keep code and operational surface minimal - repair existing mechanisms before adding replacement tools or services; avoid unnecessary abstractions, callbacks, or progress bars
- Question low-value features before adding code to support them. Rely on CLI help for obvious usage; omit repeated command reminders and command-specific title plumbing. Retain meaningful errors and recovery context.
- Keep substantive Python out of shell strings; put it in a normal `.py` file and have the shell entrypoint invoke it
- Avoid trivial helper wrappers like `def _target(name): return str(base / name)`; use `str(base / path)` directly unless the helper adds real behavior
- Keep type annotations readable: use named models for structured results instead of opaque positional tuples; use aliases when only the type expression needs a concise name.
- If a package/file/script list is just static data used once, keep it inline in the `Module(...)` or `Machine(...)` definition; only extract it when there is real logic or reuse. Keep user-edited selections one complete item per line so entries can be changed or commented independently; do not reduce configurable URLs to fragments of a shared template.
- Test business logic only: deployment decisions, data preservation, permissions, and failure handling; do not lock down UI wording/layout, retest framework behavior, or snapshot incidental personal configuration
- Git integration tests must clear inherited `GIT_*` variables before their first Git command and isolate user/system configuration. Temporary working directories alone do not isolate repository metadata or the index.
- Keep permanent tests minimal and proportionate to the behavior changed. Prefer a few focused regression cases over exhaustive combinations, large fixtures, or test scaffolding. Use temporary tests for broader one-off verification and remove them afterward; do not retain exploratory coverage by default. Reuse existing tests and the standard check entrypoint rather than expanding the suite for every edit.
- Preserve existing script phase comments, progress messages, command choices, and setup/update behavior when making focused changes
- Organize multi-step code into logical chunks with brief, action-oriented header comments, separated by blank lines. The headers should read like a recipe: a reader can understand the sequence without reading each block's implementation. Apply this to all code, not just scripts; use the section-header format below for section markers and separators. Describe meaningful steps rather than narrating every statement, and explain non-obvious constraints where needed. Group related aliases and functions by purpose, with platform checks beside the affected commands.
- Section headers use three comment lines: an `=` border, `# MARK: <Title>`, and the same border. Each border is exactly 79 characters including indentation and the comment prefix; adjust the number of `=` characters accordingly. Preserve the section's indentation and use the language's comment syntax (`// MARK: <Title>` in JSONC). Ordinary explanatory comments, recipe-step comments, and Markdown headings do not need borders.
- Put public interfaces before private helpers. Prefix module-private implementation details (helpers, classes, and constants) with `_`; keep intentionally shared interfaces public and do not access another module's private names in application code.
- Document public functions, classes, and properties with concise docstrings; do not add docstrings to private helpers. Use ordinary comments for non-obvious private implementation details.
- Keep CLI errors consistent: a short red failure summary on the error console, followed by separate dim recovery guidance when actionable. `--debug` adds dim resolution and execution traces and includes exception tracebacks. Do not configure application logging or create log files or command transcripts.
- Operations raise at the first failure with the affected item or command; do not collect failure reports or maintain ownership maps for output. Commands inherit the terminal; capture output only when a caller needs to inspect it.
- Route all application-owned Python output through functions in `app/reporting.py`, including plain values, prompts, captured command output, and tracebacks. Keep consoles private to that module. Use bold magenta `▶` headings, green `✓` success, yellow `!` warnings, red `✗` errors, and dim commands/details. Use terminal theme colors, no fixed-width decoration or tool-name prefixes. Leave framework-generated help/errors and subprocess terminal output to their existing handlers; keep plain-value commands undecorated. Announce dry-run mode once when a deployment command starts; keep action messages the same in previews and execution. Keep presentation minimal; no reporting framework or extra tracking solely for richer summaries.
- Do not add scripts whose only job is printing setup reminders; put that guidance in docs unless the script performs real work
- Keep one-time repairs of previously deployed configuration manual; do not add migration or repair steps to routine deployment.

## Homelab

- Every macOS homelab deployment requires a manual review of System Settings → General → Sharing; the owner configures shared folders, permissions, and remote access there. Keep this requirement in the shared homelab setup notes, not reminder scripts.
- Windows homelab nodes must support Windows containers and recover their services after reboot without manual intervention; automatic login is acceptable. Verify this with the chosen runtime before treating a node as ready.
- Do not SSH to, deploy to, or otherwise mutate the homelab until the user has
  reviewed the repository changes and explicitly approved deployment
- Compose projects run from their repository directories; do not maintain a
  parallel tree of service links or a custom backup engine.
- Keep service selection and storage paths in configuration. Moving a Compose
  project between supported hosts must not require application or launcher edits.
- Keep code and operational surface minimal - repair existing mechanisms before adding replacement tools or services; avoid unnecessary abstractions, callbacks, or progress bars
- Keep path/configuration changes minimal: no new tests or storage machinery; simple parent-directory checks are sufficient for interactive setup
- Use `${VAR:?}` for required shell/Compose variables, without custom error messages
- Test business logic only: deployment decisions, data preservation, permissions, and failure handling; do not lock down UI wording/layout, retest framework behavior, or snapshot incidental personal configuration
- Homelab is a single-user, Tailscale-private system: prefer minimal application login friction; never enable public exposure to achieve it
- Media acquisition uses Usenet through Weaver only
- Homelab migrations preserve existing runtime data and downloaded media for rollback; avoid extra backup trees, rollout modes, or new folder layouts unless actually required
- In Docker Compose files, keep reusable extension anchors first, group sidecars before application services, and leave named volumes last; preserve established section markers and ordering when editing
- Keep the media stack to two Compose files: app services and shared app settings in `compose.yaml`, sidecars and their state volumes in `compose.tailscale.yaml`
- In homelab discussions, "dashboard" means the Homepage service

## Documentation and Communication

Keep project reference information in its relevant architecture section; do not
add a new convention for every fix or feature, or record completed work here.

- Keep `AGENTS.md` lean: only record durable, project-wide conventions, not one-off notes for a single helper or cleanup
- All READMEs are personal working notes, not public-facing manuals: write for the task that brings the owner back, what they need to remember, and what information is already available at that point
- Give the minimum starting point for new tasks (where to create a manifest, its minimal contents, how to deploy it); keep hard-to-discover conventions and manual setup reminders, but leave configurable fields to code completion and inline documentation and link existing configs instead of duplicating examples
- Use Mermaid for useful diagrams, not ASCII art; avoid introductions, exhaustive inventories, generic tutorials, and repeated guidance across READMEs
- Do not add README navigation blocks or section-anchor cross-links; keep notes about using the system, not implementation details
- Do not turn discussion questions into documentation changes; edit docs when requested or when implementation changes invalidate existing instructions
- Keep bootstrap prerequisites limited to actions the owner must perform manually before running the command; automate supported setup in its existing owner instead of documenting extra manual work.
- Never add inline spellchecker directives to Markdown; keep spelling exceptions in `.typos.toml`, shared by the Typos CLI and editor extensions
- Before sending, remove every bullet whose deletion would not change the reader's understanding or next action
