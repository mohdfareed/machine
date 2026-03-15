# decisions.md — Decision Log
_Running log of significant decisions made. Prevents second-guessing, enables retrospectives._
_Format: Date | Decision | Context | Alternatives considered_

---

## 2026-03-04

**Architecture: Dedicated Telegram topics per category**
- Decision: Create pinned Telegram topic per category (updates, homelab, calendar, etc.) for async output delivery
- Context: Isolated cron sessions had no way to surface output to Mohammed
- Alternatives: Single thread (noisy), DM only (no threading), Discord (not used)

**Architecture: CONTEXT.md as always-current state**
- Decision: CONTEXT.md is always-current state read by every session on start
- Context: Sessions were starting stateless, missing what was active
- Alternatives: Always read MEMORY.md (too heavy for every session)

**Architecture: async output → memory files**
- Decision: All async/cron output writes to memory files first, surfaces selectively
- Context: Reduces noise; Mohammed sees summaries, not raw logs

**Privacy: MEMORY.md only in main session**
- Decision: MEMORY.md not loaded in shared/group contexts (Discord, group chats)
- Context: Contains personal context that shouldn't leak to strangers

**Autonomy: This is my laptop**
- Decision: I can run any command on the homelab without asking Mohammed first
- Context: Mohammed explicitly confirmed — workspace-internal work is autonomous

---

## 2026-03-08

**Infrastructure: ~/self-improving/ initialized**
- Decision: Use self-improving skill's memory system alongside built-in memory files
- Context: Self-improving skill provides structured self-reflection framework

**Infrastructure: BOOT.md + boot-md hook**
- Decision: Create BOOT.md to activate boot-md hook at gateway startup
- Context: Ensures consistent initialization behavior on gateway restarts

---

## 2026-03-10 (estimated)

**Repo: claudia/ branches for PRs**
- Decision: I will use `claudia/` prefixed branches for all PRs to mohdfareed/machine
- Context: Need to contribute back changes to the machine repo
- Status: Blocked — branch `claudia/updates-2026-03-10` has merge conflicts with origin/main

---

## 2026-03-13

**Reminders: remindctl confirmed working**
- Decision: Use remindctl for Apple Reminders integration (not AppleScript direct)
- Context: remindctl CLI works on homelab, HEARTBEAT.md updated to use it

---

_Add new entries as decisions are made. Format loosely — the goal is recall, not ceremony._
