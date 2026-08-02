# Raycast

This module installs Raycast and keeps a repo-owned Script Commands.

## Script Commands

Point Raycast at the repo directory directly:

- macOS: `$MC_HOME/config/raycast/commands`
- Windows: `%MC_HOME%\config\raycast\commands`

Raycast does not expose a stable, text-editable config file for script-directory
registration, so add that folder once in Raycast:

- Settings -> Extensions -> Script Commands -> Add Script Directory

## Hotkey

This module does not try to automate macOS shortcut settings. If you want
`Command-Space` for Raycast on macOS, configure it manually:

1. Set Raycast's global hotkey in Raycast Settings.
2. Disable Spotlight's conflicting shortcut in System Settings -> Keyboard ->
   Keyboard Shortcuts -> Spotlight.
