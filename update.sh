#!/usr/bin/env bash
set -euo pipefail

echo "updating pre-commit hooks..."
pre-commit autoupdate || true
