# Machine Configuration Schema

This document describes the structure and conventions for machine-specific configurations.

## Directory Structure

Each machine should have its own directory under `machines/` with the following optional files:

```
machines/{machine}/
├── zshrc              # Machine-specific shell configuration
├── zshenv             # Machine-specific environment variables
├── ssh.config         # SSH configuration for this machine
├── .gitconfig         # Git configuration overrides
├── packages.yaml       # Package definitions (see Package Format)
├── scripts/           # Machine-specific scripts
│   ├── setup.sh       # Initial setup script
│   └── *.sh           # Other utility scripts
└── README.md          # Machine-specific documentation
```

## File Purposes

### Required Files
- None (all files are optional and overlay the base configuration)

### Optional Files
- **zshrc**: Sourced after `config/shell/zshrc`, for machine-specific aliases/functions
- **zshenv**: Sourced after `config/shell/zshenv`, for machine-specific environment variables
- **ssh.config**: Included in SSH config after base SSH configuration
- **.gitconfig**: Included in Git config after base Git configuration
- **packages.yaml**: Machine-specific package requirements

## Naming Conventions

- Machine names should be lowercase, descriptive
- Use hyphens for multi-word machine names
- Scripts should have `.sh` extension
- Config files should match their target filename (e.g., `.gitconfig`)

## Environment Variables Available

All machine configurations have access to:
- `$MACHINE`: Path to the machine repository
- `$MACHINE_ID`: Current machine identifier
- `$MACHINE_PRIVATE`: Path to private configuration directory

## Best Practices

1. **Layer configurations**: Base config first, then machine-specific overrides
2. **Use conditional includes**: Check if files exist before sourcing
3. **Document machine-specific quirks**: Add comments explaining unusual configurations
4. **Keep it minimal**: Only override what's necessary for this specific machine
