# Architecture Audit: Sessions, Cron, Memory
_Written by background research agent — 2026-03-04_

## TL;DR

Cron-delivered messages are orphaned by design: they come from ephemeral isolated sessions, get pushed to Telegram as a flat message with no reply-reachable session, and are forgotten after 24h. Mohammed can't reply back into them because there's no session on the other end. This is fixable — but requires intentional architecture choices.

---

## 1. How Cron Delivers Messages

Two modes exist:

**Main session (`--session main`):**
- Enqueues a system event to the main session.
- Runs during the next heartbeat, with full main-session context.
- Output reaches the same session Mohammed is chatting in.
- Reply works: it's just the normal main session.

**Isolated session (`--session isolated`):**
- Creates a fresh session `cron:<jobId>:run:<uuid>` for each run.
- Each run starts with **no prior conversation** — blank slate.
- With `--announce`, delivers output directly to Telegram via channel adapters.
- Session is pruned after 24h by default (`cron.sessionRetention`).

Current cron jobs likely use **isolated mode** (the default for background work). The message lands in Telegram but the session it ran in is already done and will be pruned within 24h.

---

## 2. Why Replies Don't Reach the Right Session

When cron announces to Telegram:
- The message appears to come "from Claudia" but was sent directly by the Gateway's delivery layer.
- **No thread/topic binding** means it lands in the main chat, but isn't bound to any session.
- When Mohammed replies, it goes to his **main DM session** (`agent:main:main`) — not the cron session.
- The cron session (`cron:<jobId>:run:<uuid>`) is isolated, ephemeral, and doesn't listen for inbound messages.
- Even if it did — it's pruned in 24h and starts blank next run anyway.

So Mohammed replies to a ghost. The reply either hits main session context (which has no memory of the cron output) or gets processed fresh with no context.

**Root cause:** Isolated cron sessions are designed for fire-and-forget. They are not designed to receive replies.

---

## 3. Mechanisms That Exist to Fix This

### Option A: Main session cron jobs (system events)
- Use `--session main --system-event "..."` instead of isolated.
- The job injects a system event into the main session at next heartbeat.
- Output is in the main session. Mohammed can reply normally.
- **Limitation:** Main session can accumulate noise. No isolation from regular chat.

### Option B: Deliver to a dedicated Telegram topic
- Use Telegram forum topics: `delivery.to = "<chatId>:topic:<threadId>"`.
- Each topic has its own session key: `agent:main:telegram:group:<id>:topic:<threadId>`.
- Cron can consistently deliver to the same topic.
- **If Mohammed replies in that topic**, it hits the topic's session — which can have context.
- **Still an issue:** Each cron run uses a fresh isolated session even if the topic is stable. But the *topic session* persists across runs and receives Mohammed's replies.
- This is the closest thing to "always-on thread" for cron output today.

### Option C: Webhook + main session system event
- Use `delivery.mode = "webhook"` to POST to a local endpoint.
- That endpoint re-injects the content as a system event into main.
- More complex, probably not worth it.

### Option D: Skip isolated cron for status updates; use heartbeat instead
- Status updates = main session system events, not isolated jobs.
- Heartbeat already loads MEMORY.md and daily notes at startup.
- Mohammed's replies hit main session naturally.
- This is the **simplest architectural fix** for conversational continuity.

---

## 4. How Memory Can Be Shared Across Sessions

OpenClaw's memory system is **file-based** — the files outlive any session:

- `MEMORY.md` — curated long-term memory, loaded in main session
- `memory/YYYY-MM-DD.md` — daily logs, read at session start

**The problem isn't the memory system — it's that Claudia doesn't use it.**

Specifically:
- Cron jobs run isolated and don't read MEMORY.md.
- Main session reads MEMORY.md, but only if the session startup logic does it.
- Session transcript memory search exists (experimental flag) but isn't enabled.
- Pre-compaction memory flush exists — triggers when context nears limit.

**What would make it work:**
1. Cron jobs that need context should be `--session main` so they inherit MEMORY.md at startup.
2. For isolated cron jobs, write meaningful output **to a memory file** (not just Telegram delivery). Then main session picks it up.
3. Enable temporal decay + MMR in memorySearch for better recall across many daily notes.
4. Use `memory_store` tool (Mem0) for semantic facts that span sessions.

**Concrete pattern for cron → memory continuity:**
```
cron runs isolated
  → writes summary to memory/YYYY-MM-DD.md
  → announces to Telegram
Main session starts (next heartbeat or Mohammed's message)
  → reads today's daily note
  → has context of what cron did
```

---

## 5. Simplest "Always-On" Architecture

The fundamental issue: Claudia feels stateless because each interaction is a fresh blank slate. The fix is not complex — it's just discipline.

**Recommended architecture:**

### For conversational continuity (Mohammed replying to updates):
→ **Use main session system events** for status updates, not isolated cron.
```bash
openclaw cron add \
  --name "Status check" \
  --cron "0 */4 * * *" \
  --session main \
  --system-event "Run proactive status check: check email, calendar, any blocked items. Write summary to memory/YYYY-MM-DD.md." \
  --wake now
```
Mohammed's reply hits main session. Claudia has context. Problem solved.

### For noisy background jobs (don't spam main chat):
→ Use **isolated + announce to a dedicated Telegram topic** + **write to memory file**.
- Create a Telegram forum topic called "Claudia updates"
- Cron delivers there
- Mohammed can reply in that topic (hits its own stable session)
- Cron job also writes summary to `memory/YYYY-MM-DD.md` so main session knows

### For memory across sessions:
→ **Write it down. Every time.** The memory files are the only thing that survives.
- After any significant action or output: append to `memory/YYYY-MM-DD.md`
- After heartbeat checks: write findings
- During heartbeats: review recent daily notes + update MEMORY.md

### Configuration changes worth making:
1. Set `session.reset.mode = "idle"` with a long `idleMinutes` (e.g., 240) instead of daily reset at 4am — prevents context loss mid-day just because time passed.
2. Enable `memorySearch.experimental.sessionMemory = true` — lets semantic search find past conversations.
3. Enable temporal decay in memorySearch — recent notes rank higher.
4. Consider enabling pre-compaction memory flush (may already be on by default).

---

## Summary Table

| Problem | Root Cause | Fix |
|---|---|---|
| Can't reply to cron messages | Isolated sessions are ephemeral, fire-and-forget | Use main session cron or dedicated Telegram topic |
| Claudia restarts blank | Memory files not being written consistently | Write to memory/YYYY-MM-DD.md after every significant action |
| Cron has no context | Isolated sessions don't load MEMORY.md | Move status updates to main session system events |
| Sessions reset unnecessarily | 4am daily reset regardless of activity | Set idle-based reset with long window |
| No recall of past conversations | sessionMemory experimental feature disabled | Enable + configure memorySearch session indexing |

---

## Recommended Next Steps (for Mohammed's approval)

1. **Change current cron status updates** from isolated → main session system events.
2. **For any cron job that stays isolated**, add a step to write output to `memory/YYYY-MM-DD.md` so main session has context.
3. **Create a Telegram forum topic** "Claudia Updates" for isolated job delivery if isolation is desired.
4. **Tune session reset** to idle-based (4h idle) instead of daily.
5. **Enable session memory search** for semantic recall across past sessions.

None of these require code changes — all are config or behavior changes.
