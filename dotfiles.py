#!/usr/bin/env python
# Dotfiles installer/updater/manager
# Run this script with --help to see the available options

import os
import sys
import subprocess

# To remove the hassle of having to install dependencies
# for this script, it will automatically create a venv
# The main function is located in df/__init__.py
# installation/updating behavior is defined in df/module/*.py
# (e.g. df/module/git.py)


def is_in_local_venv() -> bool:
    """
    Check if the current Python interpreter is in a venv located in the same
    directory as the current script.
    """
    venv_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '.venv')
    is_in_a_venv = bool(os.environ.get("VIRTUAL_ENV"))
    if is_in_a_venv:
        current_venv_dir = os.environ.get("VIRTUAL_ENV")
        return current_venv_dir == venv_dir
    return False


def create_venv_if_needed() -> None:
    """
    Create a venv in the same directory as the current script if the current
    Python interpreter is not in a venv. It will also install the dependencies
    from requirements.txt if the venv is created or if the requirements file
    is newer than the venv.
    """
    if is_in_local_venv():
        return

    venv_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '.venv')
    venv_pip = os.path.join(venv_dir, 'bin', 'pip')
    requirements = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), 'requirements.txt')

    if not os.path.exists(venv_dir):
        # Create venv
        subprocess.check_call([sys.executable, '-m', 'venv', venv_dir])
        subprocess.check_call([venv_pip, 'install', '-r', requirements])
    elif os.path.getmtime(requirements) > os.path.getmtime(venv_dir):
        # Update venv, requirements file is newer
        subprocess.check_call([venv_pip, 'install', '-r', requirements])
        # Touch the venv directory to update its modification time
        os.utime(venv_dir, None)


def restart_with_venv() -> None:
    """
    Update the current process to run in the venv created by
    create_venv_if_needed(). This is done by replacing the current process
    """
    venv_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '.venv')
    venv_python = os.path.join(venv_dir, 'bin', 'python')
    # set the VIRTUAL_ENV environment variable to the venv directory
    os.environ['VIRTUAL_ENV'] = venv_dir
    os.execl(venv_python, venv_python, *sys.argv)

# Relaunch this script in the venv if needed

if __name__ == '__main__':
    create_venv_if_needed()
    if not is_in_local_venv():
        restart_with_venv()
        exit()  # This line is never reached


if os.environ.get("TEXTUAL"):
    # The app is launched with textual devtools
    # __name__ was not set to __main__ so we need to set it manually
    # the user allready has the venv activated so we only need to
    # set __name__ from here
    __name__ = "__main__"

if __name__ == '__main__':
    import df

    dotfiles_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(dotfiles_dir, "config.json")

    # Run the real main function
    # (the app variable is required for textual devtools)
    app = df.main(dotfiles_dir, config_file)
