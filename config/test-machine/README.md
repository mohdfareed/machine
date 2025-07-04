# Test Machine Configuration

This is a template machine configuration for testing and development.

## Structure

- `packages/` - Package files (brewfile, apt.pkg, etc.)
- `scripts/` - Machine-specific setup scripts
- Individual config files (gitconfig, zshrc, etc.)

## Usage

To create a new machine:

1. Copy this directory: `cp -r test-machine my-new-machine`
2. Modify package files in `packages/`
3. Add config files as needed
4. Add setup scripts in `scripts/`
5. Set `MACHINE=my-new-machine` and run `machine setup`
