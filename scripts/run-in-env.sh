#!/bin/bash
# run-in-env.sh - Activate the dotfiles virtual environment and run a command
# Usage: ./scripts/run-in-env.sh <command> [args...]

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the parent directory (dotfiles root)
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"
# Path to the virtual environment
VENV_DIR="$DOTFILES_DIR/.venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run './dotfiles.py --help' first to create the virtual environment."
    exit 1
fi

# Check if we have at least one argument (the command to run)
if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [args...]"
    echo "Example: $0 python ./dotfiles.py --help"
    exit 1
fi

# Activate the virtual environment and run the command
# We need to change to the dotfiles directory for proper module imports
cd "$DOTFILES_DIR"

# Source the activation script
source "$VENV_DIR/bin/activate"

# Run the provided command with all arguments
exec "$@"
