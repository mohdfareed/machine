---
name: machine-diagnosis
description: Review machine configuration or diagnose problems with tools, services, shell environments, permissions, and deployment. Compare repository intent with live machine evidence to find drift, ownership problems, or execution failures.
---

# Machine Diagnosis

Read `AGENTS.md` for project conventions and operational safety rules. Review and
diagnosis are read-only by default; do not silently repair, install, restart,
sync, or deploy configuration. Observe access restrictions even for inspection.

## Establish what is being investigated

Identify the target host, OS or WSL context, symptom or review scope, and expected
behavior. Distinguish the agent's current machine from a remote target and the
selected manifest. For repository-only reviews, state that live deployment has
not been verified rather than requiring access unnecessarily.

Start with the affected component or requested changes. Expand into dependencies
and shared targets when evidence warrants it; do not audit every file by default.

## Compare intended and actual state

Trace relevant configuration from `machines/<id>/manifest.py` and `machine.env`
through selected modules, dependencies, mappings, packages, and scripts. Inspect
applicable local setup notes. Determine which component owns the setting.

For live diagnosis, use targeted evidence: executable paths and versions, active
configuration, service/process status, permissions, network reachability, or
relevant log excerpts. Avoid broad environment or credential dumps. Separate
observed facts from assumptions, and note evidence that cannot be obtained.

For deployment questions, follow discovery, group expansion, dependency order,
platform and manager selection, and execution phases in `app/`. `mc show` shows
resolved configuration, not all runtime skips or failure paths. Check actual
manager presence queries and once/watch script state when relevant; state files
and manifests alone do not prove an operation succeeded.

## Evaluate the cause without inventing problems

Look for conflicting ownership, stale configuration, missing deployment,
platform mismatches, unmet prerequisites, and discrepancies between repository
and live state. Also consider faults in the application or external service,
not just in the bootstrapper.

Repeated declarations may be intentional overrides. Multiple writers require
examining their order and responsibility, not assuming one is dead code. Runtime
path checks can be valid prerequisites. Similar script blocks warrant a helper
only when it simplifies genuinely shared behavior. Verify stale comments against
current behavior before recommending removal.

## Report a focused next step

For each finding, give the evidence and location, practical impact, likely cause,
and smallest corrective action. Prioritize actionable findings; do not invent
issues to fill a checklist. If no problem is established, say what was checked
and which narrow observation would discriminate between the remaining causes.

Use `./scripts/check.sh` when reviewing code or configuration correctness; it is
not a substitute for live diagnosis and need not run for every operational query.
Report checks and access limitations honestly. If the user authorizes a fix,
continue with `machine-configuration` for changes, deployment, and verification.
