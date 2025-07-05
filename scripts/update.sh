#!/usr/bin/env sh
set -eu

# determine current branch
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "HEAD" ]; then
    echo "Error: Detached HEAD; cannot determine branch."
    exit 1
fi

# stash changes
echo "stashing local changes..."
stash="pre-update-$(date +%Y%m%d%H%M%S)"
git stash push --include-untracked -m "$stash"

# update repository
echo "updating..."
git fetch --all --prune
git rebase --autostash origin/"$branch"

# restore stashed changes
if git stash list | grep -q "$stash"; then
    echo "applying stashed changes..."
    git stash pop
fi

echo "update complete on branch: $branch"
