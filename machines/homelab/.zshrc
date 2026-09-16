#!/usr/bin/env zsh

# backup machine or check status of last backup
function mc::backup {
  usage="usage: $0"
  if (($# > 0)); then echo "$usage" && return 1; fi

  local job="gui/$(id -u)/com.mc.backup"
  launchctl kickstart "$job" && tail -f /tmp/mc-backup.log
}
