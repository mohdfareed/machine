# HEARTBEAT.md

## Checks (every heartbeat)

- **Overdue reminders**: ⚠️ BLOCKED — `remindctl overdue --json` denied by node security=deny. Re-enable when node exec security is loosened.
- **Upcoming events (next 2h)**: ⚠️ BLOCKED — `calendar.list` not in node allowlist. Re-enable when added to allowlist.
- **Email triage**: (pending email forwarding setup) check for urgent unread emails.

## Rules

- Don't ping for things already pinged in the last heartbeat cycle.
- Only reach out if something actually needs attention.
- Late night (23:00–08:00 America/New_York): only ping for urgent items.
