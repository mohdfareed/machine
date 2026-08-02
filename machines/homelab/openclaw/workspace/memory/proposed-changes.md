# Proposed Architecture Changes: Cron/Session Fixes
_Authored by background audit agent — 2026-03-04_

## Summary

Two cron jobs exist. Both use `sessionTarget: "isolated"` + `delivery.mode: "announce"`. This means each run is a ghost session: Claudia delivers to Telegram but Mohammed's replies land in main session with no memory of what was delivered. Proposed changes fix this.

---

## Current Cron Jobs

### 1. Daily OpenClaw recommendations check-in
- **ID:** `5ee840ad-cc80-4ab2-a904-20ca8944b988`
- **Schedule:** `30 7 * * *` (America/New_York) — 7:30 AM daily
- **sessionTarget:** `isolated`
- **payload.kind:** `agentTurn`
- **delivery.mode:** `announce`
- **Nature:** Status/advisory — this is a conversational update that Mohammed will likely want to reply to.

### 2. OpenClaw auth monitor
- **ID:** `74ece3bf-b96f-4a19-9bc9-72c34f1e72b4`
- **Schedule:** `0 8 * * *` (America/New_York) — 8:00 AM daily
- **sessionTarget:** `isolated`
- **payload.kind:** `agentTurn`
- **delivery.mode:** `announce`
- **Nature:** Status/alert — if auth is expiring, Mohammed needs to act and will likely reply or follow up.

---

## Session Reset: Current State

The main config (`openclaw.json`) has **no explicit `session.reset` config**, and `agents.json5` shows no reset config either. This means session reset likely uses the **OpenClaw default**, which is a **daily time-based reset** (typically 4am). This causes context loss mid-day if the reset fires while a conversation is in progress.

There is no `idleMinutes` or `idle`-based reset visible in any config file.

---

## Proposed Changes

### Change 1: Convert both cron jobs to main session system events

Both jobs are status-update-style and benefit from continuity with main session. Mohammed should be able to reply naturally.

**For job 5ee840ad (Daily OpenClaw check-in):**
```bash
openclaw cron update 5ee840ad-cc80-4ab2-a904-20ca8944b988 \
  --session-target main \
  --payload-kind systemEvent
```

Or via API/config JSON diff:
```json
// Before:
"sessionTarget": "isolated",
"payload": { "kind": "agentTurn", ... },
"delivery": { "mode": "announce" }

// After:
"sessionTarget": "main",
"payload": {
  "kind": "systemEvent",
  "message": "Daily check-in: review OpenClaw improvements (tools/config/workflow), what changed since last check, recommended next action, and any approval-needed items. Reply with a concise morning summary — do not use the message tool."
},
"delivery": { "mode": "announce" }
```

**For job 74ece3bf (Auth monitor):**
```json
// Before:
"sessionTarget": "isolated",
"payload": { "kind": "agentTurn", ... },
"delivery": { "mode": "announce" }

// After:
"sessionTarget": "main",
"payload": {
  "kind": "systemEvent",
  "message": "Run `openclaw models status --check` and reply with a short auth health report. If any provider is near expiry, expired, or needs reauth, clearly label it and provide the exact next action. Do not use the message tool."
},
"delivery": { "mode": "announce" }
```

**Effect:** Both jobs inject a system event into the main session. The main session wakes, runs the task with full MEMORY.md context, and delivers the output to Telegram from the main session. Mohammed's replies then naturally reach the main session.

---

### Change 2: Add idle-based session reset to agents.json5

Currently there is no session reset config — OpenClaw default likely resets at a fixed daily time, which can interrupt mid-day context.

**Add to `/Users/claudia/.openclaw/config/agents.json5`:**
```json5
// Agents - workspace and behavior
{
  "defaults": {
    "model": {
      // ... existing model config unchanged ...
    },
    "workspace": "~/.openclaw/workspace",
    "heartbeat": {
      "every": "10m"
    },
    // ADD THIS:
    "session": {
      "reset": {
        "mode": "idle",
        "idleMinutes": 240
      }
    }
  }
}
```

**Effect:** Session resets only after 4 hours of inactivity instead of on a daily schedule. Active conversations won't lose context mid-day.

---

### Change 3 (Optional / Lower Priority): Enable session memory search

If OpenClaw supports it, enabling semantic session memory allows recall across past conversations.

**Add to `openclaw.json` or `agents.json5`:**
```json5
"memorySearch": {
  "experimental": {
    "sessionMemory": true,
    "temporalDecay": true
  }
}
```

**Effect:** Claudia can find relevant past conversations via semantic search, not just today's daily note. Mohammed won't need to re-explain context from days ago.

---

### Change 4 (Behavioral, No Config): Write cron output to daily memory file

Even after converting to main session, good hygiene is to append summaries to `memory/YYYY-MM-DD.md` so future sessions have the record. This is a **behavioral/prompt change**, not a config change.

**Prompt addition for both cron jobs (append to message):**
```
After completing the check, append a 1-3 sentence summary of key findings to memory/YYYY-MM-DD.md (use today's date).
```

---

## Priority Order

| # | Change | Risk | Impact |
|---|--------|------|--------|
| 1 | Convert both cron jobs to `sessionTarget: main` + `kind: systemEvent` | Low | High — fixes reply continuity immediately |
| 2 | Add idle-based session reset (4h idle) | Low | Medium — prevents mid-day context wipe |
| 3 | Add memory-write step to cron job prompts | None | Medium — builds continuity over time |
| 4 | Enable experimental session memory search | Unknown | Medium — long-term recall |

---

## What NOT to Change

- `delivery.mode: "announce"` is correct for both jobs — keep it.
- `wakeMode: "now"` is correct — keep it.
- `schedule` and `agentId` — no changes needed.

---

## How to Apply Change 1 (When Approved)

The `openclaw cron` CLI doesn't have an `update` subcommand (only `list`, `add`, `delete`, `run`). Changes must be made by:

1. Delete the existing job: `openclaw cron delete <id>`
2. Re-add with updated flags: `openclaw cron add --name "..." --cron "..." --session main --system-event "..." --announce`

Or, if direct JSON editing of the cron store is supported (check `/Users/claudia/.openclaw/cron/`), edit the job JSON directly.

Check: `ls /Users/claudia/.openclaw/cron/`
