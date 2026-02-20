# Git platform config for Windows.

@"
[core]
    autocrlf = true
[credential]
    helper = manager
"@ | Set-Content -Path "$HOME\.gitconfig.platform" -Encoding utf8NoBOM
