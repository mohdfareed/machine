# Claudia Setup Notes (WIP)

## Goal
Treat this container as Claudia's workstation for repo work + OpenClaw-assisted operations.

## Current capability snapshot
- Workspace git available ✅
- Internet egress for git clone ✅
- Node/npm/pnpm/python available ✅
- OpenClaw CLI available ✅
- Docker CLI not usable (permission denied) ⚠️
- GitHub CLI `gh` not usable (permission denied) ⚠️
- Tailscale CLI not usable (permission denied/off in-container) ⚠️

## Repo onboarding
- Cloned: `projects/machine`
- Remote: `https://github.com/mohdfareed/machine.git`
- Default branch: `main`

## Proposed operating pattern (draft)
1. Do analysis/dev changes locally in container + workspace.
2. Keep changes in feature branches with patch summaries.
3. Ask Mohammed before any external-impact action (push/deploy/outbound messages/config that affects running systems).
4. For actions faster for Mohammed to do directly, ask with one crisp instruction.

## Next checks (small chunks)
- Repo-specific bootstrap/docs read for machine/homelab workflow.
- Determine reproducible test paths available in-container.
- Define PR/branch convention optimized for quick review.
