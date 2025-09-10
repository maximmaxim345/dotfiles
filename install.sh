#!/bin/bash
# DevContainer dotfiles installation script
# Installs essential dotfiles modules for development containers

set -e

# Prefer POSIX sh-safe behavior for external commands
SHELL_CHECK=1

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
print_info "Starting DevContainer dotfiles installation..."

# Helpers for distro detection and package installation (Debian/Ubuntu & Alpine)
ensure_root() {
    if [ "${EUID:-$(id -u)}" -ne 0 ]; then
        if command -v sudo >/dev/null 2>&1; then
            SUDO=sudo
        else
            SUDO=
        fi
    else
        SUDO=
    fi
}

detect_distro() {
    if [ -f /etc/alpine-release ]; then
        DISTRO=alpine
    elif [ -r /etc/os-release ] && grep -qiE "(debian|ubuntu)" /etc/os-release; then
        DISTRO=debian
    else
        DISTRO=unknown
    fi
}

install_system_packages() {
    case "$DISTRO" in
        alpine)
            print_info "Detected Alpine. Installing python3, py3-pip and py3-virtualenv via apk..."
            ${SUDO:-} apk add --no-cache python3 py3-pip py3-virtualenv || return 1
            ;;
        debian)
            print_info "Detected Debian/Ubuntu. Installing python3, python3-pip and python3-venv via apt..."
            ${SUDO:-} apt-get update -qq
            DEBIAN_FRONTEND=noninteractive ${SUDO:-} apt-get install -y python3 python3-pip python3-venv || return 1
            ;;
        *)
            print_warning "Unknown distro; please ensure python3, pip and venv support are installed manually."
            ;;
    esac
}

install_github_cli() {
    case "$DISTRO" in
        alpine)
            # GitHub CLI is not available in Alpine's main repos, try to install via alternative method
            print_info "Attempting to install GitHub CLI for Alpine..."
            if ! ${SUDO:-} apk add --no-cache github-cli 2>/dev/null; then
                print_warning "GitHub CLI not available in Alpine repositories. Skipping installation."
                print_info "You can install it manually later if needed: https://cli.github.com/"
                return 0
            fi
            ;;
        debian)
            print_info "Installing GitHub CLI for Debian/Ubuntu..."
            DEBIAN_FRONTEND=noninteractive ${SUDO:-} apt-get install -y gh || return 1
            ;;
        *)
            print_warning "Unknown distro; GitHub CLI installation skipped."
            ;;
    esac
}

ensure_python3_available() {
    # Prefer python3 binary explicitly
    if command -v python3 >/dev/null 2>&1; then
        PY=python3
    elif command -v python >/dev/null 2>&1; then
        # only accept python if it is actually python3
        if python -c 'import sys; sys.exit(0) if sys.version_info[0] == 3 else sys.exit(1)'; then
            PY=python
        else
            PY=python3
        fi
    else
        PY=python3
    fi

    if ! command -v "$PY" >/dev/null 2>&1; then
        print_info "No python3 binary found, attempting to install system packages..."
        ensure_root
        detect_distro
        install_system_packages || print_warning "Automatic install failed; please install python3, pip and venv manually."
    fi

    # If venv support missing, attempt to install system packages
    if ! "$PY" -c 'import venv' >/dev/null 2>&1; then
        print_info "python venv support missing; attempting to install system packages providing venv support..."
        ensure_root
        detect_distro
        install_system_packages || print_warning "Failed to install venv support automatically."
    fi
}

create_and_activate_venv() {
    if [ ! -d ".venv" ]; then
        print_info "Creating .venv using ${PY} -m venv .venv"
        "$PY" -m venv .venv
    fi
    # shellcheck disable=SC1091
    . .venv/bin/activate
    pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
}

# Sanity check: ensure we're in repo root
if [ ! -f "dotfiles.py" ]; then
    print_error "dotfiles.py not found. Please run this script from the dotfiles directory."
    exit 1
fi

print_info "Preparing environment and ensuring python3/pip/venv are available..."
ensure_python3_available
create_and_activate_venv

# Ensure GitHub CLI (gh) is present; attempt to install if it's missing
if ! command -v gh >/dev/null 2>&1; then
    print_info "GitHub CLI (gh) not found; attempting to install via package manager..."
    ensure_root
    detect_distro
    install_github_cli || print_warning "Automatic gh install failed; please install GitHub CLI manually (https://cli.github.com/)."
fi

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
# Use python3 explicitly to avoid accidentally running Python 2 if `python` points to it
if "$PY" dotfiles.py --quiet --continue-on-error install "${MODULES[@]}"; then
    print_success "DevContainer dotfiles installation completed successfully!"
else
    exit_code=$?
    print_warning "Installation completed with some errors (exit code: $exit_code)"
    print_info "Some modules may have failed to install, but essential ones should be working."
fi

print_info "Installation summary:"
"$PY" dotfiles.py list --installed

print_success "DevContainer setup complete! 🎉"
print_info "You may need to reload your shell or restart your terminal to see all changes."
