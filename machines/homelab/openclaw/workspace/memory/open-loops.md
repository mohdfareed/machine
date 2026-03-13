# open-loops.md — Everything Active

_Last updated: 2026-03-13 19:05 EST_
_Any session can read this to know what's going on._

## Active cron jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| Self-improvement loop | 2am nightly | Research, learn, improve AGENTS.md/config autonomously |
| Repo sync — pull | Every 30min | Pull Mohammed's changes from machine repo |
| Repo sync — PR | 3am nightly | Batch commit my changes, open PR |
| OpenClaw daily check | 7:30am | (existing, needs to be rewired to topic thread) |
| Auth monitor | 8:00am | (existing, needs to be rewired to topic thread) |

## ⚠️ Overdue Reminders — surface in next morning brief (2026-03-13)
- **Schedule dermatologist appointment** (Personal) — overdue since 2026-01-12. Dr: Beth H Lertzman, MD, 585-424-6770
- **Schedule Behavior Health appointment** (Personal) — overdue since 2026-02-25. Phone: 585-922-9230
- **Grocery Shopping** (Chores) — overdue since 2026-01-26 (likely stale/needs reset)
- Multiple recurring Wed chore reminders — stale since Jan, likely need date reset not action


- Branch `claudia/updates-2026-03-10` has conflicts with `origin/main` when rebasing
- Conflicting files: `machines/homelab/openclaw/cron/jobs.json`, `machines/homelab/openclaw/workspace/MEMORY.md`, `machines/homelab/openclaw/workspace/memory/2026-03-04.md`
- Repo left in clean state (rebase aborted). Branch is behind origin/main until resolved.
- Options: (a) merge instead of rebase, (b) resolve conflicts manually, (c) reset branch to main and re-apply changes

## Pending: needs Mohammed
- [ ] Approve PRs I open on `mohdfareed/machine`
- [ ] Branch protection may block pushes — confirm if claudia/ branches are allowed

## Pending: my work
- [x] Read self-improving and continuity-framework skills (done 2026-03-08 nightly session)
- [x] Initialize ~/self-improving/ directory structure (done 2026-03-08)
- [x] Create memory/questions.md for continuity-framework pattern (done 2026-03-08)
- [x] Create BOOT.md to activate boot-md hook at gateway startup (done 2026-03-09)
- [ ] Rewire existing cron jobs to deliver to dedicated Telegram topics instead of isolated sessions
- [ ] Create dedicated Telegram topics (one per category)
- [ ] Test apple-calendar-cli skill
- [x] Wire Apple Reminders into heartbeat checks (done 2026-03-13 — remindctl works, HEARTBEAT.md unblocked)
- [x] Read learning-dump.md and integrate findings into AGENTS.md (done 2026-03-04)
- [ ] Build out contacts.md as people come up in conversations
- [ ] Start using waiting-for.md to track pending items from Mohammed

## Decisions made (2026-03-04)
- Dedicated pinned Telegram topic per category for proactive updates
- All async output writes to memory files
- CONTEXT.md = always-current state, read by every session on start
- No accountability theater — only write it down if it changes future behavior
- Mohammed uses Apple ecosystem (Mail, Calendar, Reminders, Notes)
- This is MY laptop — I can run anything without asking Mohammed first
