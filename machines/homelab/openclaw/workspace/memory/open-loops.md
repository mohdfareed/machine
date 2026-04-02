## Repo Sync Blocker (stale after 2026-03-17 — surface in Monday brief)
2026-03-15 — Repo sync failed: local unstaged changes preventing git pull --rebase from origin/claudia/updates-2026-03-10.

Details:
- Command: git pull --rebase origin claudia/updates-2026-03-10
- Error: "cannot pull with rebase: You have unstaged changes. Please commit or stash them."

Files reported as modified locally in `git status --porcelain` output (examples):
- machines/homelab/openclaw/cron/jobs.json
- machines/homelab/openclaw/openclaw.json
- machines/homelab/openclaw/workspace/CONTEXT.md
- machines/homelab/openclaw/workspace/MEMORY.md
- machines/homelab/openclaw/workspace/memory/2026-03-14.md
- machines/homelab/openclaw/workspace/memory/open-loops.md
- machines/homelab/openclaw/workspace/memory/questions.md
- machines/homelab/openclaw/workspace/memory/waiting-for.md

Suggested next steps (pick one):
1) Review and commit the local changes, then re-run: git pull --rebase origin claudia/updates-2026-03-10
2) Stash changes (git stash push -m "cron/auto-stash 2026-03-15") and run the pull; then apply stash and resolve any conflicts.
3) If these local changes are accidental, discard them (git reset --hard) and pull.

If you want, I can:
- create a branch with the local changes and push it for review
- stash, pull, and apply the stash, then report any conflicts
- leave this for you to handle

— Claudia (automated repo-sync)
