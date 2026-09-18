# Working on My Machine

## Understand the task first

Follow the current project's instructions and existing patterns. Treat requested
outcomes as requirements, not tools mentioned while exploring options. For a
question or design discussion, explain the recommendation before implementing it.
Prefer the smallest maintainable change; preserve unrelated work.

## Use the machine's existing setup

When a task depends on machine-specific paths, tools, shell behavior, or settings,
load the `machine-context` skill.
Use `mc show home` to locate the machine configuration repository rather than
assuming a checkout path. Ordinary project work does not require a machine audit.

Distinguish the current host, Windows or WSL context, and saved machine selection.
Verify relevant live state instead of treating configuration as proof of setup.
Agent shells may lack interactive aliases, functions, or environment variables;
check the actual executable and shell before changing configuration.

Before changing managed settings, find their owner in the machine repository and
read its instructions. Inspect symlink targets before editing installed dotfiles.
Keep project-specific work in its own repository, not in machine configuration.

## Keep changes and access deliberate

A request for repository edits is not permission to deploy them. Do not install,
sync, restart services, or weaken permissions merely to investigate a problem.
Do not SSH to, deploy to, or otherwise mutate the homelab until I have reviewed
the repository changes and explicitly approved deployment.

Keep credentials, private environment values, and generated agent state local.
Do not dump entire environments or private files into output. Use established
secret integrations only when needed for the task.

Report what changed, what was actually verified, and what remains uncertain.
Distinguish repository edits from live deployment, and attempted checks from
passing checks. Keep explanations concise and correct mistaken assumptions
rather than agreeing with them.
