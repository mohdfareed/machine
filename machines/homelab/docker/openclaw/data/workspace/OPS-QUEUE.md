# OPS-QUEUE.md

## Active / Pending

- Overnight deep-dive: OpenClaw docs + community usage patterns + MCP/skills/plugins landscape.
- Prepare tomorrow-morning recommendation brief (tools/config changes to consider, with priorities and tradeoffs).
- Define Claudia git workflow in `projects/machine`:
  - branch naming
  - commit frequency
  - approval gate before push/deploy
- Decide proactive reporting cadence:
  - event-driven only
  - or lightweight periodic digest
- Build homelab operations backlog from `machine` repo exploration.
- Set up voice workflow for hands-free collaboration (cooking/exercise).

## Done

- Identity set: name `Claudia`, emoji `🦉`.
- Communication preference captured: short conversational style, clear start/finish signals.
- Approval policy captured: explicit approval for external-impact actions; internal workspace work autonomous.
- Workspace persistence model chosen:
  - workspace as curated persistent area
  - `projects/` for active clones/sandboxes
  - `.gitignore` guardrails added
- Removed nested `workspace/.git` repo (backed up under `.trash/`).
- `machine` repo cloned locally for exploration (`workspace/projects/machine`).
