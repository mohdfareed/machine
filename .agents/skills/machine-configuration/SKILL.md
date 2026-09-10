---
name: machine-configuration
description: Create or change machine configuration, install or configure tools and services, and deploy or update machines using this repository. Use for both repository changes and live machine setup.
---

# Machine Configuration

Read `AGENTS.md` for ownership, platform, validation, and operational safety rules.

## Establish the target and scope

Identify the requested host, its OS or WSL context, and whether the task authorizes
repo changes, live changes, or both. Check the selected machine and checkout when
relevant; a local `mc status` does not identify a remote host. Resolve uncertainty
before mutation, and follow the project's access and deployment approval rules.

Read the relevant `machines/<id>/manifest.py`, `machine.env`, modules, and setup
notes. Inspect only the live state needed to understand what is already installed
or configured. Do not equate a declaration with successful deployment.

## Give the change an owner

Find the existing mechanism before adding one. Shared configuration belongs in
`config/`; host-specific policy belongs in `machines/<id>/`. Keep secrets and
runtime data machine-local. Use the environment tiers and declared package
managers rather than introducing parallel installation or secret-loading paths.

Distinguish durable configuration from a temporary troubleshooting adjustment or
manual application authorization. Do not commit generated application state or
force every live change into a manifest. Check current model fields and nearby
examples instead of inventing configuration options.

## Make and check the smallest change

Preserve unrelated edits and existing data. Consider every platform that includes
the affected module. Follow existing phase ordering, dependency, and permission
mechanisms; inspect the runner when their behavior matters.

For repository edits, run `./scripts/check.sh` and reuse proportionate existing
tests. Use `mc show -m <id>` to inspect resolved configuration, not as proof of
runtime behavior. Do not deploy merely to validate code changes.

## Deploy within the authorized scope

Choose the operation deliberately: `mc deploy` deploys the current checkout,
`mc update` performs maintenance, and `mc sync` integrates canonical main before
deploying. Check the target checkout and local changes before syncing. Module
filters still include shared core setup; do not assume they isolate all effects.

Before execution, explain material risks such as restarts, elevation, access
changes, or data migration. Obtain any required approval under `AGENTS.md`; a
request to edit configuration is not permission to deploy it. Prefer existing
entrypoints over manually duplicating their work.

## Verify the result

Check the affected behavior on the target: the service, command, link, permission,
or setting the user actually needed. A successful exit code alone is insufficient.
If execution fails, establish what completed before retrying; preserve recovery
data and avoid blindly rerunning the whole setup.

Finish with what changed in the repo, what was deployed to which host, what was
verified, and any remaining manual step. Clearly distinguish changes not yet deployed
from live results.
