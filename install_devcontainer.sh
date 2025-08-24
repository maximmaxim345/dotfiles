#!/bin/bash
# DevContainer dotfiles installation script
# Installs essential dotfiles modules for development containers

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the dotfiles directory
if [ ! -f "dotfiles.py" ]; then
    print_error "dotfiles.py not found. Please run this script from the dotfiles directory."
    exit 1
fi

print_info "Starting DevContainer dotfiles installation..."

# Modules to install (excluding GUI applications and system-specific tools)
MODULES=(
    "bash_config"
    "lazygit"
    "nvim_config_lazyvim"
    "starship"
    "starship_config"
    "zoxide"
    "zsh_config"
)

print_info "Installing ${#MODULES[@]} essential modules for DevContainer..."

# Install modules with continue-on-error to be resilient
if python dotfiles.py --quiet --continue-on-error install "${MODULES[@]}"; then
    print_success "DevContainer dotfiles installation completed successfully!"
else
    exit_code=$?
    print_warning "Installation completed with some errors (exit code: $exit_code)"
    print_info "Some modules may have failed to install, but essential ones should be working."
fi

print_info "Installation summary:"
python dotfiles.py list --installed

print_success "DevContainer setup complete! 🎉"
print_info "You may need to reload your shell or restart your terminal to see all changes."
