# Dev Machine (`mc`)

Cross-platform machine bootstrapper and dotfile manager.

> **Agent instruction:** This file contains project-specific conventions,
> constraints, and preferences that shape how you work on this codebase.
> When the user states a preference or rule ("never do X", "always use Y"),
> add it here. When the project changes in a way that contradicts an existing
> note, update or remove it. Do this proactively - don't wait to be asked.
>
> Use Codex memories for cross-session context. This file is for durable coding
> standards, not session notes. Keep repo-specific Codex skills under
> `.agents/skills/`; keep portable global Codex configuration in
> `config/codex/` and mutable runtime state machine-local.
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

- `app/cli/` - CLI entrypoint, separate apply/update/sync commands, info commands, and shared reporting
- `app/models.py` - Runtime settings, configuration models, and operation results
- `app/logging.py` - Shared consoles and logging
- `app/discovery.py` - Machine, module, and script discovery
- `app/machine.py` - Module/manifest loading, dependency resolution, and validation
- `app/env.py` - Runtime settings, platform detection, shared environment, and login-shell env file
- `app/shell.py` - Command execution via `run(..., capture_output=...)`, PATH refresh, and sudo caching
- `app/ops/` - File, package, and script deployment; manager-specific mechanics in `managers.py`
- `config/` - Shared dotfiles and configs
- `machines/` - Per-host configurations
- `scripts/bootstrap.sh` / `scripts/bootstrap.ps1` - Bare-machine bootstrap

## Commands

- `./scripts/check.sh` - Non-mutating validation entrypoint (always use this to validate)
- `./scripts/fix.sh` - Format, auto-fix lint, and normalize script permissions before re-running checks
- `uv run mc --help` - Run CLI in dev
- `mc sync` fetches canonical `mohdfareed/machine` main, integrates with Git's
  fast-forward-only merge with autostash, then applies the current checkout.
  Tracked local edits are restored before apply; ahead commits and detached HEAD
  are allowed. Git failures or autostash restoration conflicts stop before apply.
  Never discard local changes; leave conflicting auto-stashes for recovery with Git.
  Branches, commits, pushes, and PRs belong to Git.

## Architecture

### Module (`config/<path>/module.py`)

Module names are dotted paths relative to `config/`: `tools/docker/module.py`
is `tools.docker`. Discovery recurses through grouping folders, stopping at
module directories; folder names cannot contain dots. Files and scripts resolve
relative to the module directory.

Exports a `Module(files, packages, scripts, depends)`. All fields use simple
types - `depends` and manifest `modules` are `list[str]` (module names).
Scripts under `scripts/` are auto-discovered; explicit `scripts=` list
is only needed for files outside that directory. `depends=["other"]`
auto-includes prerequisite modules in manifests (deduped, ordered before
the dependent).

### Manifest (`machines/<id>/manifest.py`)

Exports a `Machine(pkg_managers, modules, files, packages, scripts)`.
Composes modules and adds machine-specific overrides. Manifest `modules` entries
match an exact module name or all dotted descendants of a grouping name:
`tools` matches `tools` and `tools.*`, not `toolsmith`. Expansion uses discovery
order, then existing dependency ordering and deduplication; no matches is an error.
CLI filters and module `depends` still use exact module names.

### Cross-Platform Requirements

- Always verify Windows compatibility when touching files, paths, or scripts
- Use `Platform.is_a()` for platform-family matching: WSL matches Linux and Unix; macOS and Linux match Unix. Keep these relationships in the enum.
- Windows SSH client is OpenSSH (built into Windows 10+): supports `~`, `IgnoreUnknown`
- Unix shell files and ShellCheck configuration use LF line endings
- Shell scripts need platform tags (`.unix.sh` / `.win.ps1`) - never assume Unix-only
- Path separators: use `pathlib.Path` in Python; avoid hardcoded `/` in target strings

### Packages and Files

- The `core` module is always included, including module-filtered runs, and owns setup shared by every machine. OS settings and features belong in the explicitly selected `system` module. Machine manifests explicitly declare `pkg_managers: list[PkgManager]`; never infer or install managers from package usage or PATH. `BREW` includes casks. Validate manager platform compatibility and declaration dependencies in Python before running scripts; setup scripts only perform installation. Package installation and manager maintenance may use only declared managers; custom scripts must follow the same policy.

- Define packages with `Package(...)` directly; package helper constructors (`brew(...)`, `apt(...)`, etc.) are removed
- `FileMapping(mode=...)` owns mapped-file permissions; owner-only modes use a current-user and SYSTEM ACL on Windows
- Use `FileMapping(platforms=...)` for intentionally platform-specific files instead of conditionally constructing file lists
- Use `cask=` for Homebrew casks; package source selection is platform-aware and should replace package-level `if PLATFORM ...` conditionals in manifests/modules
- Use package `platforms=` only when a package is intentionally restricted or script-only; normal multi-manager package selection should not need manifest-level platform conditionals
- `mc apply` only installs missing packages; upgrades belong to `mc update`. If a package exists but is not managed by the requested manager, `mc apply` should still install it with that manager
- Script-only packages use `Package.name` as the installed-command check during `mc apply`; `mc update` re-runs script-backed packages

### Script Pipeline and Environment

- Platform tags on scripts: `name.macos.sh`, `name.unix.sh`, `name.win.ps1`
- Script prefixes: `once_` = run once, `watch_` = re-run on file change, `init_` = run before packages, `up_` = run only during `mc update`, `_` = helper (never auto-executed, sourced by other scripts)
- Execution order: files → declared manager setup → remaining `init_*` scripts → packages → remaining scripts
- `~/.env` is the only generated file - written by `mc apply` with just `MC_HOME` and `MC_ID`
- Three-tier script environment (`app.env.build_env`):

  1. `~/.env` - generated by `mc apply`, contains only `MC_HOME` and `MC_ID`
  2. `$MC_HOME/machines/$MC_ID/machine.env` - committed config vars (paths, hostname, ...)
  3. `$MC_PRIVATE/env/$MC_ID.env` - secrets, one file per machine, plain dotenv

- `mc` loads all three tiers into every script subprocess - scripts should NOT re-source them
- Shell profiles load the first two tiers; `secrets` explicitly loads the private tier on demand
- `machine.env` uses plain `KEY=VALUE` (no `export`); values may reference earlier vars
- `MC_PRIVATE` defaults to `app_dir/private`; `machine.env` may override (e.g. `$ICLOUD/.machine`)
- Scripts skip gracefully when `MC_PRIVATE` directory doesn't exist
- State file: `app_dir/state.json` tracks script runs; package presence is determined from the requested package manager at apply time

`build_env` prepares shared variables and shell-specific additions together
before execution. When PowerShell is available, it extends `PSModulePath` with the bundled
`MachineAdmin` module while preserving existing module paths and `-File` execution.
Elevation is explicit through `Invoke-Admin { ... }`; pass outside values using
`param(...)` and `-ArgumentList` because elevated blocks run in a separate process. Elevated text output and errors
are relayed to the caller for terminal display and logging.

### Configuration Ownership and State

Give configuration one owner: shared setup belongs in modules, host-specific setup
belongs in machine manifests. Commit portable configuration; keep credentials,
runtime state, caches, and machine-generated application data local.

- Machine extras: `extra.zsh` → `~/.zshrc.local`
- Repo root derived from `Path(__file__).parents[1]` in `app/models.py` - no env var needed
- App data: `typer.get_app_dir("mc")` for logs/state; define runtime file paths once in `Settings` and reuse them in readers, writers, and CLI commands
- Workspace-local editor config lives in `.vscode/` for VS Code and `.zed/` for Zed only for repo-specific file associations and context servers; personal editor defaults belong in `config/vscode/` and `config/zed/`
- VS Code Remote Tunnels are owned by the `vscode` module; account authorization remains a one-time manual step on each machine
- The `codex` module owns the Codex CLI, unified ChatGPT desktop app, and portable `~/.codex/config.toml`; credentials, pairing/enrollments, live databases, histories, caches, downloaded plugins, and generated memories stay machine-local
- Editor tasks should avoid ad hoc external tool dependencies; prefer shell builtins or repo-managed entrypoints so tasks stay portable across machines
- Shared repo policy should prefer cross-editor files (`pyproject.toml`, `.editorconfig`, `.shellcheckrc`, `.markdownlint.json`, `.cspell.json`) over editor-specific settings
- Standalone services own their code, tests, dependencies, documentation, and internal directory setup; this repo owns only deployment wiring and host prerequisites

## Coding Conventions

- Before writing new code, check the codebase for existing patterns and follow them
- Always keep the happy path flat: handle alternative, skip, and failure paths first with early `return`, `continue`, `break`, or exceptions as appropriate, then let the main path proceed without unnecessary nesting or `else`. Apply this throughout control flow, not just validation; preserve required cleanup and shared follow-up work.
- Keep code and operational surface minimal - repair existing mechanisms before adding replacement tools or services; avoid unnecessary abstractions, callbacks, or progress bars
- Keep substantive Python out of shell strings; put it in a normal `.py` file and have the shell entrypoint invoke it
- Avoid trivial helper wrappers like `def _target(name): return str(base / name)`; use `str(base / path)` directly unless the helper adds real behavior
- Keep type annotations readable: use named models for structured results instead of opaque positional tuples; use aliases when only the type expression needs a concise name.
- If a package/file/script list is just static data used once, keep it inline in the `Module(...)` or `Machine(...)` definition; only extract it when there is real logic or reuse
- Test business logic only: deployment decisions, data preservation, permissions, and failure handling; do not lock down UI wording/layout, retest framework behavior, or snapshot incidental personal configuration
- Keep permanent tests minimal and proportionate to the behavior changed. Prefer a few focused regression cases over exhaustive combinations, large fixtures, or test scaffolding. Use temporary tests for broader one-off verification and remove them afterward; do not retain exploratory coverage by default. Reuse existing tests and the standard check entrypoint rather than expanding the suite for every edit.
- Preserve existing script phase comments, progress messages, command choices, and setup/update behavior when making focused changes
- Organize multi-step code into logical chunks with brief, action-oriented header comments, separated by blank lines. The headers should read like a recipe: a reader can understand the sequence without reading each block's implementation. Apply this to all code, not just scripts; use the section-header format below for section markers and separators. Describe meaningful steps rather than narrating every statement, and explain non-obvious constraints where needed.
- Section headers use three comment lines: an `=` border, `# MARK: <Title>`, and the same border. Each border is exactly 79 characters including indentation and the comment prefix; adjust the number of `=` characters accordingly. Preserve the section's indentation and use the language's comment syntax (`// MARK: <Title>` in JSONC). Ordinary explanatory comments, recipe-step comments, and Markdown headings do not need borders.
- Prefix module-private implementation details (loggers, helpers, classes, and constants) with `_`; keep intentionally shared interfaces public and do not import another module's private names in application code.
- Document public functions, classes, and properties with concise docstrings; do not add docstrings to private helpers. Use ordinary comments for non-obvious private implementation details.
- Keep CLI errors consistent: a short red failure summary on the error console, followed by separate dim recovery guidance when actionable. Keep technical details in plain-text logs; do not embed Rich markup in log messages.
- Do not add scripts whose only job is printing setup reminders; put that guidance in docs unless the script performs real work

## Homelab

- Do not SSH to, deploy to, or otherwise mutate the homelab until the user has
  reviewed the repository changes and explicitly approved deployment
- `MC_HOMELAB_DIR` is required for homelab scripts and is declared in the
  machine's committed `machine.env`; never silently fall back to `~/.homelab`
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
- Give the minimum starting point for new tasks (where to create a manifest, its minimal contents, how to apply it); keep hard-to-discover conventions and manual setup reminders, but leave configurable fields to code completion and inline documentation and link existing configs instead of duplicating examples
- Use Mermaid for useful diagrams, not ASCII art; avoid introductions, exhaustive inventories, generic tutorials, and repeated guidance across READMEs
- Do not add README navigation blocks or section-anchor cross-links; keep notes about using the system, not implementation details
- Do not turn discussion questions into documentation changes; edit docs when requested or when implementation changes invalidate existing instructions
- Never add inline spellchecker directives to Markdown; keep spelling exceptions in `.cspell.json`
- Before sending, remove every bullet whose deletion would not change the reader's understanding or next action
