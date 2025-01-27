# Machine Setup

[![CI](https://github.com/mohdfareed/machine/actions/workflows/ci.yml/badge.svg)](https://github.com/mohdfareed/machine/actions/workflows/ci.yml) [![CD](https://github.com/mohdfareed/machine/actions/workflows/cd.yml/badge.svg)](https://github.com/mohdfareed/machine/actions/workflows/cd.yml) <a><img alt="Coverage" src="https://img.shields.io/badge/Coverage-94%25-brightgreen.svg" /></a>

Machine setup and configuration CLI app.

**Requirements:**

- Python 3.9.6+
-

## Installation

```sh
# install with poetry (installs at the provided path)
repo="https://raw.githubusercontent.com/mohdfareed/machine/refs/heads/main"
curl -fsSL $repo/scripts/deploy.py | python3 - [-h] [-p PATH] [branch]
```

where `PATH` is the path to download the machine CLI app.
Defaults to `~/.machine`.

### Development

```sh
# clone the repository
git clone https://github.com/mohdfareed/machine.git
cd machine

# setup environment
./scripts/dev.py
```

### Releases

The package can be installed from the latest release with pipx using:

```sh
repo="https://raw.githubusercontent.com/mohdfareed/machine/main"
pipx install $(curl -fsSL $repo/scripts/release.sh | sh -)
```

## Usage

```sh
machine-setup --help
```
