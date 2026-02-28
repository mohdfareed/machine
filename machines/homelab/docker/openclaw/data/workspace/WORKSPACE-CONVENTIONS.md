# Workspace Conventions

## Purpose
Keep this workspace clean and intentional for long-term collaboration.

## Layout
- `projects/` → active repo clones/sandboxes (ignored by default)
- workspace root docs/scripts → curated artifacts we want to persist
- `.openclaw/`, `.trash/` → local runtime/recovery (ignored)

## Workflow
1. Do active engineering inside `projects/<repo>`.
2. Capture stable decisions in root docs (plans, runbooks, checklists).
3. Only promote intentional changes into tracked files.
4. External-impact actions (deploy/push/outbound comms) require Mohammed approval.
