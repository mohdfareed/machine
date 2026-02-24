# Configuration Audit

Read AGENTS.md for project conventions, then audit every file under `config/`
and `machines/` for violations. Run `./scripts/test.sh` at the end.

## Audit Methodology

These are the patterns that cause real problems in this codebase:

1. **Shared module scripts must work on every machine that includes the module.**
   If a script only applies to some machines, it belongs in `machines/<id>/scripts/`,
   not in the module's `scripts/` directory. Watch for hardcoded path probes
   (checking if a file exists at runtime to decide behavior) — that's always a
   sign the logic is in the wrong place.

2. **No duplicate ownership.** A package, file target, or env var should be
   declared in exactly one place. Check for the same package appearing in both
   a module and a manifest, or in two different modules.

3. **Scripts that write to the same target file are conflicts, not features.**
   If two scripts touch the same path (e.g., `~/.env`), one of them is dead
   code. Find it.

4. **Copy-pasted blocks across scripts are DRY violations.** Use `_`-prefixed
   helper scripts (auto-skipped by the runner) and `source` them.

5. **Stale comments are lies.** `REVIEW` or `TODO` comments that reference
   resolved or outdated issues should be updated or removed.

6. **`mc show` is the source of truth for run order.** If something looks like
   it might run in the wrong order, verify against `mc show` output. Module
   items run before machine items within each phase.

## Output Format

For each issue: file path, line numbers, what's wrong, severity
(HIGH/MEDIUM/LOW), and a concrete fix. End with a summary table sorted by
severity. If nothing is found, say so — don't invent problems.
