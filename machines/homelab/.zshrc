#!/usr/bin/env zsh

# re-deploy by stashing -> pulling main -> back-merging
function mc::deploy {
  usage="usage: $0"
  if (($# > 0)); then echo "$usage" && return 1; fi
  pushd "$MC_HOME" >/dev/null || return 1

  local did_stash=0
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git stash push -u -m "mc::deploy" || { popd >/dev/null; return 1; }
    did_stash=1
  fi

  git fetch origin main && git merge origin/main
  local rc=$?

  (( did_stash )) && git stash pop
  popd >/dev/null
  return $rc
}
