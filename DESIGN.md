# Bootstrap Tool Design Document

## 1. Overview

A unified **Tools ↔ Machines** bootstrap system to manage a small fleet of devices (macOS, Linux, Windows) with:

* **Code** (CLI app) fully decoupled from **Config** (dotfiles, packages, overrides, secrets)
* Minimal dependencies on fresh hosts (only Git & Python 3)
* Developer convenience via `uv` and pre-commit hooks

## 2. Core Concepts

### 2.1 Tools

* Nouns representing installable components (e.g. `git`, `zsh`, `vscode`, `brew`)
* Each has:

  * **Logic** (`app/tools/<tool>/logic.py`) that:

    * Knows OS-specific destination paths
    * Links defaults → home or config paths
    * Applies machine overrides
    * Runs tool-specific commands
  * **Defaults** (`config/tools/<tool>/defaults/`)
  * **Package specs** (`config/tools/<tool>/packages.txt`, `extensions.txt`)

### 2.2 Machines (Hosts)

* Nouns representing individual device profiles (e.g. `work`, `personal`, `gaming`)
* Each has under `config/hosts/<host>/`:

  * `tools.txt`: list of tool names to install
  * `packages.txt`: one-line-per-manager specs (`apt git gh`, `snap code --classic`, etc.)
  * `configs/`: overrides for tool defaults (e.g. `gitconfig`, `zshenv`)
  * `scripts/`: ordered shell scripts for post-install tasks (`01-ssh.sh`)
* **Secrets**: `config/hosts/<host>/secrets/` (gitignored) holds `.env`, SSH keys, etc.

## 3. Directory Structure

```
bootstrap-tool/
├── .host                     # current host
├── app/                      # application code (Python package)
│   ├── cli.py                # subcommands: install-cli, install, host, tools, update
│   ├── orchestrator.py       # install_tools, install_packages, run_scripts, self_update
│   ├── utils.py              # link/junction, run_cmd, parse_packages, detect_os
│   └── tools/                # per-tool logic modules
│       ├── git/logic.py
│       ├── zsh/logic.py
│       └── vscode/logic.py
└── config/                   # data & config
    ├── tools/                # per-tool defaults & specs
    └── hosts/                # per-host definitions & overrides
        └── <host>/
            ├── tools.txt
            ├── packages.txt
            ├── configs/
            ├── scripts/
            └── secrets/      # gitignored: .env, keys/
```

## 4. Workflows

### 4.1 Deployment (fresh host)

1. **Sync secrets**: copy `machine-private/<host>/` → `~/machine-private/<host>`
2. **Clone repo**: `git clone ... ~/bootstrap-tool && cd ~/bootstrap-tool`
3. **Set host & private path**:

   ```bash
   echo <host> > .host
   export MACHINE_PRIVATE=~/machine-private
   ```
4. **Install CLI**: `./bs install-cli` (stdlib venv + `pip install -e .`)
5. **Bootstrap machine**: `bs install --private "$MACHINE_PRIVATE"`

### 4.2 Development

1. **Dev venv**: `bash scripts/dev.py` uses `uv` to create `./.venv` + install `[dev]` extras
2. **Pre-commit**: `uv run pre-commit install`
3. **Testing & lint**: `uv run nox -s tests`, `uv run nox -s lint`
4. **CLI iteration**: edit `app/` code, run `bs <subcommand>` via `uv run bs ...`

## 5. Secrets Handling

* **Templates** in `config/hosts/<host>/secrets.template/.env.example`
* **Real secrets** in `config/hosts/<host>/secrets/` (gitignored)
* **Loading**:

  * Python: `python-dotenv` in orchestrator
  * Shell: optional `source ~/.config/.../.env` or `direnv`
* **SSH keys**: linked into `~/.ssh/id_rsa`, `ssh-add`-ed

## 6. Conventions & Standards

* **XDG Base Directories** for config (`$XDG_CONFIG_HOME/bs/...`)
* **OS detection** in `utils.detect_os()`
* **Permissions**: `chmod 700` for dirs, `600` for keys/env
* **PEP 517** build-system:

  ```toml
  [build-system]
  requires=["setuptools>=61.0","wheel"]
  build-backend="setuptools.build_meta"
  ```

---

**This document** gives you everything you need (layout, workflows, conventions) to implement the bootstrap tool without further design. Good luck! Enjoy building!
