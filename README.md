# Machine Setup

Machine setup and configuration CLI app.

## Installation

```sh
# install with poetry (installs poetry at the machine path)
repo="https://raw.githubusercontent.com/mohdfareed/typer-machine/main"
curl -fsSL $repo/scripts/deploy.py | sh - [machine_path]
```

where `machine_path` is the path to install the machine CLI app.
Defaults to `~/.machine`.

### Development

```sh
# clone the repository
git clone https://github.com/mohdfareed/typer-machine.git
cd typer-machine

# setup environment
./setup.sh --dev
```

### Releases

The package can be installed from the latest release with pipx using:

```sh
repo="https://raw.githubusercontent.com/mohdfareed/typer-machine/main"
pipx install $(curl -fsSL $repo/scripts/release.sh | sh -)
```

## Usage

```sh
machine-setup --help
```
