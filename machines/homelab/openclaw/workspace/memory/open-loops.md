# open-loops.md — Everything Active

_Last updated: 2026-03-10 02:00 EST_
_Any session can read this to know what's going on._

## Active cron jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| Self-improvement loop | 2am nightly | Research, learn, improve AGENTS.md/config autonomously |
| Repo sync — pull | Every 30min | Pull Mohammed's changes from machine repo |
| Repo sync — PR | 3am nightly | Batch commit my changes, open PR |
| OpenClaw daily check | 7:30am | (existing, needs to be rewired to topic thread) |
| Auth monitor | 8:00am | (existing, needs to be rewired to topic thread) |

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
- [ ] Wire Apple Mail/Calendar/Reminders into heartbeat checks
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
