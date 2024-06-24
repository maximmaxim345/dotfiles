#!/bin/bash
# This script installs paru, an AUR helper, on Arch Linux or compatible distributions.

set -e

sudo pacman -S --needed --noconfirm git

# Function to clean up on error
cleanup() {
	echo "An error occurred. Cleaning up..."
	rm -rf "$temp_dir"
	exit 1
}

# Trap specific signals and errors
trap cleanup ERR INT TERM

# Create a temporary directory
temp_dir=$(mktemp -d)

git clone https://aur.archlinux.org/paru.git "$temp_dir/paru"

# Install base-devel package
sudo pacman -S --needed base-devel --noconfirm

# Compile and install paru
cd "$temp_dir/paru" && makepkg -si --noconfirm

# Clean up
rm -rf "$temp_dir"

echo "Paru installation completed successfully."
