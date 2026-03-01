# HOMELAB.md — Homelab Architecture & Ops Reference

_Last updated: 2026-03-01 by recon subagent_

---

## Overview

Always-on macOS machine (Mac Mini / MacBook in clamshell) running Docker services exposed via Tailscale. Infrastructure-as-code in `github.com/mohdfareed/machine`, cloned locally at `projects/machine`. CLI tool is `mc` (Python/uv). No reverse proxy — each internet-facing service has its own Tailscale sidecar container.

---

## Services Running

| Service | Stack | Access | Notes |
|---|---|---|---|
| **OpenClaw** | Custom Docker image | `openclaw.<tailnet>.ts.net` (funnel, public) | Personal AI assistant — this container |
| **KBM Personal** | `ghcr.io/mohdfareed/kbm` | `kbm.<tailnet>.ts.net/personal` (funnel) | Knowledge base memory, OpenAI-powered |
| **KBM Work** | `ghcr.io/mohdfareed/kbm` | `kbm.<tailnet>.ts.net/work` (funnel) | Same image, separate data |
| **OpenMemory (mem0)** | `mem0/openmemory-mcp` + `mem0/openmemory-ui` | UI: `mem0.<tailnet>.ts.net` (tailnet-only), MCP: port 8443 (funnel) | AI memory layer; backed by Qdrant |
| **Qdrant** | `qdrant/qdrant` | Internal only (no Tailscale sidecar) | Vector store for OpenMemory/mem0 |
| **Homepage** | `ghcr.io/gethomepage/homepage` | Host loopback :3000 → `tailscale serve` | Homelab dashboard; Docker socket read-only |
| **Discord-Telegram Bot** | Custom build from `mohdfareed/discord-telegram-bot` | Internal only | Bridges Discord ↔ Telegram |

---

## How Deployment Works

### `mc` CLI
- `mc apply <machine>` — deploys configs, symlinks files, installs packages, runs scripts
- `mc update` — runs `up_*` scripts (system updates, brew cleanup, DNS flush)
- `mc sync` — git pull + push

### File Layout
```
~/.machine/
├── config/<module>/      # shared modules (git, shell, homelab, openclaw, …)
└── machines/homelab/     # homelab-specific manifest + docker/ services
```

### Docker Deploy Flow
1. `docker.unix.sh` creates `~/.homelab/<svc>/` on host
2. Symlinks compose files from repo into `~/.homelab/<svc>/`
3. `docker compose up -d`
4. Runtime data (`data/`, `logs/`) stays in `~/.homelab/` — never committed

### Secrets Flow (3-tier)
1. `~/.env` → `MC_HOME`, `MC_ID`
2. `machines/homelab/machine.env` → committed config vars (paths, hostnames)
3. `$MC_PRIVATE/env/homelab.env` → machine secrets (API keys, tokens); lives in iCloud at `$ICLOUD/.machine`

Service-specific secrets in `MC_PRIVATE/docker/<service>.env`.

### Networking Patterns
| Pattern | How | Services |
|---|---|---|
| Internet (funnel) | Tailscale sidecar container per service | OpenClaw, KBM, OpenMemory MCP |
| Tailnet-only | Host loopback port + `tailscale serve` | Homepage, OpenMemory UI |
| Internal | No sidecar, no ports | Qdrant, Discord-Telegram bot |

---

## OpenClaw Setup Specifics

### Container
- Based on `ghcr.io/openclaw/openclaw:latest` with Homebrew (Linux) layered on top
- Volumes: `./data` → `/home/node/.openclaw` (all persistent state)
- Named volumes: `openclaw-brew`, `openclaw-npm` (tool caches)
- Network: via `ts-openclaw` Tailscale sidecar

### Config Architecture
`openclaw.json` is an include-only hub; actual config split into:
- `config/agents.json5` — model: `github-copilot/claude-sonnet-4.6`, heartbeat every 30m
- `config/channels.json5` — Telegram (polling mode; webhook disabled due to port 8787 conflict)
- `config/plugins.json5` — active plugins list
- `config/skills.json5` — installed skills
- `config/hooks.json5` — internal hooks (boot-md, command-logger, session-memory, bootstrap-extra-files)

### Active Plugins
- `telegram` — primary channel
- `device-pair` — node pairing
- `llm-task` — background LLM tasks
- `lobster` — unknown/experimental
- `openclaw-mem0` — **active memory provider** (OSS mode, Qdrant backend on `mem0.<tailnet>.ts.net:6333`)
- `voice-call` — voice call support

Memory plugins disabled: `memory-core`, `memory-lancedb`

### Active Skills
apple-notes, apple-reminders, clawhub, coding-agent, github, healthcheck, himalaya, mcporter, nano-banana-pro (Gemini), nano-pdf, openai-image-gen, openai-whisper-api, peekaboo, skill-creator, summarize, tmux, voice-call

### Cron Jobs
1. **Daily OpenClaw recommendations** — 7:30 AM ET: morning check-in with improvements/approval-needed items
2. **Auth monitor** — 8:00 AM ET: `openclaw models status --check` auth health report

### Telegram Channel
- Polling mode (not webhook — webhook disabled; known port 8787 conflict in container)
- `dmPolicy: pairing`, `allowFrom: [TELEGRAM_USER_ID]`
- Streaming: partial

### TTS / Voice
- Provider: ElevenLabs
- Voice call plugin enabled with streaming

### Model Config
- Primary: `github-copilot/claude-sonnet-4.6`
- Fallbacks: anthropic, openai-codex, google gemini, github-copilot gpt-mini

---

## Backups

- **launchd job** (`com.mc.backup.plist`) runs daily at 04:30 (after 04:00 scheduled wake)
- Pulls `~/.homelab/*/data/` and `.env` from all remote servers via rsync over Tailscale SSH
- Lands in `$MC_PRIVATE/backups/<hostname>/<service>/`
- `MC_PRIVATE` is in iCloud → automatic cloud sync
- Homelab Mac itself covered by Time Machine

---

## Known Issues / Needs Attention

1. **Telegram webhook disabled** — running in polling mode due to unknown port 8787 conflict in container. Should investigate and fix to enable proper webhook mode.
2. **Docker CLI unavailable in container** — Claudia can't run `docker` commands directly (permission denied). Ops requiring Docker must be done by Mohammed on the host.
3. **GitHub CLI (`gh`) unavailable in container** — same permission issue.
4. **Tailscale CLI unavailable in container** — can't check tailscale status from inside container.
5. **mem0 OSS sqlite3 issue (resolved)** — `disableHistory: true` workaround applied; the plugin was patched at `~/.openclaw/extensions/openclaw-mem0/index.ts`. This patch is not in the Dockerfile — a rebuild would lose it.
6. **HEARTBEAT.md is empty** — heartbeat currently does nothing; no periodic checks scheduled.
7. **OPS-QUEUE items pending** — several items in OPS-QUEUE.md not yet completed (see Ops Backlog below).

---

## Prioritized Ops Backlog

### P1 — Reliability / Active Issues
1. **Fix Telegram webhook** — investigate port 8787 conflict in ts-openclaw container; switch from polling to webhook for lower latency and proper operation
2. **Bake mem0 patch into Dockerfile** — the `disableHistory` fix in `openclaw-mem0/index.ts` is ephemeral; will be lost on container rebuild. Add to Dockerfile or upstream it
3. **Define Claudia git workflow** — branch naming, commit frequency, approval gate before push/deploy (from OPS-QUEUE)

### P2 — Ops / Visibility
4. **Populate HEARTBEAT.md** — define what periodic checks to run (email, calendar, system health)
5. **Proactive reporting cadence** — decide event-driven vs periodic digest (from OPS-QUEUE)
6. **Morning brief improvement** — current daily cron sends recommendations; consider consolidating with auth monitor into a single morning digest

### P3 — Capability Expansion
7. **Voice workflow** — set up hands-free collaboration (cooking/exercise use case, from OPS-QUEUE)
8. **OpenClaw docs deep-dive** — `overnight deep-dive` item from OPS-QUEUE; review capabilities, MCP/skills/plugins landscape, prepare config recommendations
9. **Homepage Tailscale widget** — `services.yaml` references Tailscale API key and device IDs; verify widgets are rendering correctly
10. **KBM personal knowledge base** — populated? Verify data exists in `~/.homelab/kbm/data/`

### P4 — Hygiene
11. **Review openclaw-mem0 plugin version** — v0.1.2 was installed; check if updates available
12. **Review model fallback chain** — some model IDs in `agents.json5` may be stale/fictional; validate against `openclaw models status`
13. **Codex/copilot-cli packages on homelab** — `manifest.py` installs `copilot-cli` and `codex` brew packages; ensure these are intended and up to date

---

## Key File Paths Quick Reference

| What | Path |
|---|---|
| `mc` repo | `~/.machine/` (on homelab host) / `projects/machine` (in this container) |
| OpenClaw data dir | `~/.openclaw/` (in container) = `machines/homelab/docker/openclaw/data/` |
| OpenClaw main config | `~/.openclaw/openclaw.json` |
| OpenClaw config dir | `~/.openclaw/config/` |
| Workspace | `~/.openclaw/workspace/` |
| Docker services (host) | `~/.homelab/<service>/` |
| Homelab manifest | `machines/homelab/manifest.py` |
| Homelab docker services | `machines/homelab/docker/` |
| Secrets | `$MC_PRIVATE/env/homelab.env` (iCloud, not in repo) |
| Backups | `$MC_PRIVATE/backups/` (iCloud) |
| Dockerfile | `machines/homelab/docker/openclaw/Dockerfile` |
