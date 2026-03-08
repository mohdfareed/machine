# HEARTBEAT.md

## Checks (every heartbeat)

- **Overdue reminders**: ⚠️ BLOCKED — `remindctl overdue --json` denied by node security=deny. Re-enable when node exec security is loosened.
- **Upcoming events (next 2h)**: ⚠️ BLOCKED — `calendar.list` not in node allowlist. Re-enable when added to allowlist.
- **Email triage**: (pending email forwarding setup) check for urgent unread emails.
- **Open loops sweep**: Scan `memory/open-loops.md` — surface anything stale >3 days or newly blocked.
- **Questions surfacing**: Check `memory/questions.md` — if a question has been pending >3 days, bring it up naturally.

## Rules

- Don't ping for things already pinged in the last heartbeat cycle.
- Only reach out if something actually needs attention.
- Late night (23:00–08:00 America/New_York): only ping for urgent items.
- Batch similar alerts into one message — don't send multiple pings for related issues.

## Morning Heartbeat (~8-9 AM)
If nothing else is urgent, send a brief "here's what's on your plate" only if there's actually something on the plate.
Don't send a morning brief if there's nothing to say.

## Weekly (Sunday or Monday)
Sweep recent daily logs → update MEMORY.md → surface stale open loops.
