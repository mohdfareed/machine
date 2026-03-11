# HEARTBEAT.md

## Checks (every heartbeat)

- **Overdue reminders**: ⚠️ BLOCKED — `remindctl overdue --json` denied by node security=deny. Re-enable when node exec security is loosened.
- **Upcoming events (next 2h)**: ⚠️ BLOCKED — `calendar.list` not in node allowlist. Re-enable when added to allowlist.
- **Email triage**: (pending email forwarding setup) check for urgent unread emails.
- **Open loops sweep**: Scan `memory/open-loops.md` — surface anything stale >3 days or newly blocked.
- **Questions surfacing**: Check `memory/questions.md` — if a question has been pending >3 days, bring it up naturally.

## Stale Item Protocol

When an item in `memory/waiting-for.md` is past its "Stale after" date:
1. Include it in the next morning heartbeat message (not a separate ping)
2. Format: "⏳ Still waiting on [item] from [person] (added [date])"
3. After surfacing, update the "Stale after" date by +4 days so it doesn't repeat until then
4. Don't re-surface if Mohammed acknowledged it in the current conversation

When `memory/open-loops.md` has a pending item with no activity for >7 days: surface it in morning brief as "🔲 No movement on: [item]"

## Value Threshold — When to Surface vs Stay Silent

Before sending anything proactively, score it:

| Score | Meaning | Example |
|-------|---------|---------|
| 5 | Urgent / time-sensitive | Meeting in 30 min, deadline today |
| 4 | Actionable and timely | Stale waiting-for, unresolved blocker |
| 3 | Useful but not urgent | Something interesting to know |
| 2 | Low value / noise | Confirming something already known |
| 1 | Nothing | No new information |

**Rule: Only surface items scoring ≥ 4 in a proactive ping.** Score 3 items can be batched into the morning brief if there's already a reason to message. Scores 1–2 = stay silent (HEARTBEAT_OK).

When multiple items: surface highest-value first, batch the rest in one message. Never send multiple pings for the same heartbeat cycle.

## Rules

- Don't ping for things already pinged in the last heartbeat cycle.
- Only reach out if something actually needs attention.
- Late night (23:00–08:00 America/New_York): only ping for urgent items (score 5).
- Batch similar alerts into one message — don't send multiple pings for related issues.

## Morning Heartbeat (~8-9 AM)
If nothing else is urgent, send a brief "here's what's on your plate" only if there's actually something on the plate.
Don't send a morning brief if there's nothing to say.

## Weekly (Sunday or Monday)
Sweep recent daily logs → update MEMORY.md → surface stale open loops.
