# Machine Setup & Dotfiles

## Requirements

- Python 3.9.6+ (macOS default)

### macOS

```sh
xcode-select --install
sudo xcodebuild -license accept
```

## TODO

- Update `README.md`
- Update copilot instructions

- SSH:
    - Load ssh keys from private dir and set permissions
    - Add keys to agent
    - Keychain integration
    - Key pair generation

- Others:
    - Change default shell to zsh/pwsh
    - Hostname configuration
    - WSL support

- CI/CD:
    - Restore python formatting checks in ci
    - Add update script for updating dependencies during cd
