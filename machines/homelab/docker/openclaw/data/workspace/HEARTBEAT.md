# HEARTBEAT.md

## Checks (every heartbeat)

- **Overdue reminders**: run `remindctl overdue --json` on homelab Mac node, ping Mohammed if anything is due.
- **Upcoming events (next 2h)**: check calendar for events in the next 2 hours; if any have a location, spin up a cron job for a "leave in X" ping at the right time.
- **Email triage**: (pending email forwarding setup) check for urgent unread emails.

## Rules

- Don't ping for things already pinged in the last heartbeat cycle.
- Only reach out if something actually needs attention.
- Late night (23:00–08:00 America/New_York): only ping for urgent items.
