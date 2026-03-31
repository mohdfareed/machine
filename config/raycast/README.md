# Raycast

This module installs Raycast and keeps a repo-owned Script Commands directory in
`$MC_HOME/config/raycast/config/script-commands`.

## Script Commands

Point Raycast at the repo directory directly:

- macOS: `$MC_HOME/config/raycast/config/script-commands`
- Windows: `%MC_HOME%\config\raycast\config\script-commands`

Raycast does not expose a stable, text-editable config file for script-directory
registration, so add that folder once in Raycast:

- Settings -> Extensions -> Script Commands -> Add Script Directory

## ChatMock

[`chatmock`](https://github.com/RayBytes/ChatMock)
allows Raycast to use OpenAI Codex for its AI features.
The module installs `chatmock` with `uv tool install` for Raycast-specific use.

1. Run `chatmock login` once in a terminal.
2. In Raycast, run the `Start ChatMock` script command.

## Hotkey

This module does not try to automate macOS shortcut settings. If you want
`Command-Space` for Raycast on macOS, configure it manually:

1. Set Raycast's global hotkey in Raycast Settings.
2. Disable Spotlight's conflicting shortcut in System Settings -> Keyboard ->
   Keyboard Shortcuts -> Spotlight.
