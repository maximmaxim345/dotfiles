#!/bin/bash
# This script installs paru, an AUR helper, on Arch Linux or compatible distributions.
# It creates a temporary user if run as root and cleans up after the installation.

set -e

# Function to generate a random username
generate_username() {
	echo "user_$(tr -dc 'a-zA-Z0-9' </dev/urandom | fold -w 8 | head -n 1)"
}

# Function to run commands as the specified user
run_as_user() {
	if [[ $EUID -eq 0 ]]; then
		su - "$username" -c "$1"
	else
		eval "$1"
	fi
}

# Function to clean up on error
cleanup() {
	echo "An error occurred. Cleaning up..."
	if [[ $EUID -eq 0 ]]; then
		userdel -r "$username" 2>/dev/null || true
	fi
	rm -rf "$temp_dir"
	exit 1
}

# Trap specific signals and errors
trap cleanup ERR INT TERM

# Create a temporary directory
temp_dir=$(mktemp -d)

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
	# Create a new random user account with a temporary home directory
	username=$(generate_username)
	useradd -m -d "$temp_dir/home" "$username"
	chown "$username:$username" "$temp_dir"
else
	username=$USER
fi

run_as_user "git clone https://aur.archlinux.org/paru.git $temp_dir/paru"

# Install base-devel package
if [[ $EUID -eq 0 ]]; then
	pacman -S --needed base-devel --noconfirm
else
	sudo pacman -S --needed base-devel --noconfirm
fi

# Compile paru as the user
run_as_user "cd $temp_dir/paru && makepkg -s"

# Install paru
if [[ $EUID -eq 0 ]]; then
	pacman -U --noconfirm *.pkg.tar.*
else
	sudo pacman -U --noconfirm *.pkg.tar.*
fi

# Clean up
rm -rf "$temp_dir"

# Remove the temporary user if created
if [[ $EUID -eq 0 ]]; then
	userdel -r "$username"
fi

echo "Paru installation completed successfully."
