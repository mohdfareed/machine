# OPS-QUEUE.md

## Active / Pending

- **Set up dedicated Apple ID for Claudia on homelab Mac** - sign homelab Mac into Claudia's Apple ID, then share relevant calendars/reminder lists/notes from Mohammed's personal account. This keeps a clean security boundary without manual access management.


- Read through `projects/machine` repo and build homelab operations context.
- Define git workflow (branch naming, commit frequency, approval gate before push/deploy).
- Decide proactive reporting cadence (event-driven vs periodic digest).
- Set up voice workflow for hands-free collaboration (cooking/exercise).
- Add Gemini billing to enable nano-banana-pro image generation.
- Install `memo` on Mac for Apple Notes access (brew tap antoniorodr/memo && brew install antoniorodr/memo/memo).

## Done

- Identity set: name `Claudia`, emoji `🦉`.
- Communication preference captured: short conversational style, clear start/finish signals.
- Approval policy captured: explicit approval for external-impact actions; internal workspace work autonomous.
- Workspace persistence model chosen: `projects/` for active clones, workspace root for curated artifacts, `.gitignore` guardrails added.
- Removed nested `workspace/.git` repo (backed up under `.trash/`).
- `machine` repo cloned locally at `workspace/projects/machine`.
- Phase 1 security hardening: credentials perms fixed to 700, hooks verified, daily auth-monitor cron added.
- Daily morning check-in cron set for 07:30 America/New_York.
- Confirmed Apple Reminders (`remindctl`) already installed on Mac node.
- Verified OpenAI image gen works (DALL-E/gpt-image-1 ✅, Gemini quota exhausted ❌).
