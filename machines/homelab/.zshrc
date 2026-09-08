#!/usr/bin/env zsh

# backup machine or check status of last backup
function mc::backup {
  usage="usage: $0 -s|--start"
  if (($# > 1)); then echo "$usage" && return 1; fi

  if [[ "$1" == "-s" || "$1" == "--start" ]]; then
    # start backup now
    launchctl kickstart gui/$(id -u)/com.mc.backup
  else
    # check backup status
    launchctl print gui/$(id -u)/com.mc.backup
  fi
}

# pull machine by stashing -> pulling main -> back-merging
function mc::pull {
  usage="usage: $0"
  if (($# > 0)); then echo "$usage" && return 1; fi
  pushd "$MC_HOME" >/dev/null || return 1

  local did_stash=0
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git stash push -u -m "mc::deploy" || { popd >/dev/null; return 1; }
    did_stash=1
  fi

  git fetch origin main && git merge origin/main && git push
  local rc=$?

  (( did_stash )) && git stash pop
  popd >/dev/null
  return $rc
}
