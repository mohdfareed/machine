# Skills Setup — 2026-03-04

## Summary

Checked and tested: apple-reminders, apple-notes. No calendar skill found.

---

## ✅ apple-reminders — WORKING

- **CLI:** `remindctl` (installed at `/opt/homebrew/bin/remindctl`)
- **Status:** Fully functional. `remindctl list` returns lists; `remindctl today` works.
- **Permissions:** Reminders access is granted (no prompt, returns data).
- **Notes:** Found 2 reminders in a list. Ready to use.

### Test result
```
remindctl list     → "Reminders ⚠️ — 2 reminders"
remindctl today    → "No reminders found" (today has none)
```

---

## ❌ apple-notes — NEEDS INSTALL

- **CLI:** `memo` — **NOT installed**
- **Install command:** `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- **Status:** Binary missing. Skill is registered but unusable until installed.
- **Permissions needed after install:** System Settings → Privacy & Security → Automation → grant Notes.app access.

### 🚩 ACTION REQUIRED (Mohammed)
Install memo to enable Apple Notes management:
```bash
brew tap antoniorodr/memo && brew install antoniorodr/memo/memo
```
Then approve the Automation permission prompt when first run.

---

## ℹ️ Calendar Skill — NOT AVAILABLE

- `ls skills/ | grep -i cal` returned only `voice-call` — no Apple Calendar skill exists.
- No calendar CLI skill is installed in OpenClaw.
- Mohammed uses Apple Calendar (mentioned in USER.md). A calendar skill may be worth adding if/when available on ClawHub.

---

## Skill Locations

| Skill | Path |
|-------|------|
| apple-reminders | `/opt/homebrew/lib/node_modules/openclaw/skills/apple-reminders/SKILL.md` |
| apple-notes | `/opt/homebrew/lib/node_modules/openclaw/skills/apple-notes/SKILL.md` |
