# BOOT.md — Gateway Startup Checklist

_This file is read by the `boot-md` hook at every gateway startup._
_Keep it short. These are the most essential startup checks._

## On every gateway start:

1. **Read CONTEXT.md** — understand current state before doing anything.
2. **Check `memory/open-loops.md`** — are there any items with stale waiting-for deadlines? Flag anything overdue.
3. **Check `memory/waiting-for.md`** — flag any items where "stale after" date has passed.
4. **If the time is 7:30–9:30 AM local:** Prepare a morning brief. Check calendar, email, and weather if relevant. Send a proactive summary to Mohammed if there's anything worth saying. Don't send if there's nothing new.
5. **Update `memory/YYYY-MM-DD.md`** with a one-line note that the gateway started and any flags found.

## Do NOT:
- Send messages to Mohammed for routine startup unless there's a genuine flag.
- Re-read all memory files exhaustively — just CONTEXT.md and open-loops.md.
- Run email or calendar checks if the time is between 10 PM and 7 AM.

---
_BOOT.md is intentionally minimal. Gateway boots happen frequently._
