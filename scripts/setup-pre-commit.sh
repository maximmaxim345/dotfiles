#!/usr/bin/env bash
set -euo pipefail

# Script to set up pre-commit using the repository's local .venv
# Usage: ./scripts/setup-pre-commit.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$REPO_ROOT/.venv/bin/python"
VENV_BIN="$REPO_ROOT/.venv/bin"

if [ ! -x "$VENV_PY" ]; then
  echo "ERROR: venv python not found at $VENV_PY"
  echo "Create the venv first by running the project normally, or run: python -m venv .venv"
  exit 1
fi

echo "Upgrading pip and installing tools into .venv..."
"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install pre-commit black isort ruff

echo "Installing pre-commit git hook..."
"$VENV_BIN/pre-commit" install

echo "Running pre-commit on all files (this may auto-fix some files)..."
"$VENV_BIN/pre-commit" run --all-files || true

echo "Done. If you want to run formatters manually, use: $VENV_BIN/black <paths>"
