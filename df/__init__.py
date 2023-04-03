import os
import glob
import importlib.util
import df
import df.ui
import df.config
from df.config import ModuleConfig
from pathlib import Path
import shutil
import requests

DOTFILES_DIR: str # The directory where the dotfiles are stored, can be used by modules
DOTFILES_PATH: Path # The path to the dotfiles directory

# Helper function usefull for installing and uninstalling modules

def find_backup_path(original: Path) -> Path:
    """Find a non existing path for backuping a old
    configuration file/folder
    Will return the original path appeneded with ".old" or
    ".old1", ".old2".
    """
    location = original.parent
    name = original.name
    backup_path = location / (name + ".old")
    i = 1
    while backup_path.exists():
        backup_path = location / (name + f".old{i}")
        i += 1
    return backup_path

def is_backup_required(path: Path) -> bool:
    """Check if the given path should be backuped
    Returns true if the path is a file, a non empty folder
    or a symlink
    Returns false if it can be safely deleted
    """
    if path.is_file():
        return True
    if path.is_dir():
        for _ in path.iterdir():
            # The folder is not empty
            return True
    if path.is_symlink():
        return True
    return False

def delete_or_unlink(path: Path, delete_recursively: bool = False) -> bool:
    """Delete the given path or unlink it if it is a symlink,
    if the path does not exist, do nothing
    If delete_recursively is true, will delete the path recursively
    Returns true if the path was deleted, false if it did not exist
    """
    if not path.exists():
        return False
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        if delete_recursively:
            shutil.rmtree(path)
        else:
            path.rmdir()
    else:
        # Unkown type, throw an error
        raise ValueError(f"Unknown path type: {path}")
    return True

def ensure_parent_exists(path: Path) -> None:
    """Ensure that the parent directory of the given path exists
    """
    parent = path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

def move_path(source: Path, target: Path) -> None:
    """Move the source path to the target path.
    Will work with files, symlinks, folders and over filesystem boundaries,
    will delete the target if it exists
    """
    # Use shutil move, ensure parent exists, delete target if needed
    if not delete_or_unlink(target):
        ensure_parent_exists(target)
    shutil.move(source, target)

def symlink_path(source: Path, target: Path) -> None:
    """Symlink the source path to the target path"""
    # Use pathlib symlink, ensure parent exists
    # TODO: Windows support
    ensure_parent_exists(target)
    target.symlink_to(source)

def create_backup(path: Path, config: ModuleConfig, key: str) -> None:
    """Create a backup of the given path if needed
    Will save the backup path in the config under the given key,
    can be used to restore with restore_backup
    """
    if is_backup_required(path):
        backup_path = find_backup_path(path)
        move_path(path, backup_path)
        config.set(key, str(backup_path))
    elif path.exists() and path.is_dir():
        # The folder is empty, we can just delete it, we just need to
        # note that we deleted a empty folder
        path.rmdir()
        # Use a magic value to indicate that we deleted a empty folder
        config.set(key, "@@@empty@@@")
    else:
        # Note that no backup was created
        config.unset(key)

def restore_backup(path: Path, config: ModuleConfig, key: str) -> None:
    """Restore a backup of the given path
    If available, will restore the given path as it was before calling
    create_backup, this will delete/unlink the current path
    """
    # Delete the current path
    delete_or_unlink(path)
    backup_path = config.get(key)
    if backup_path is None:
        # No backup was created, do nothing
        pass
    elif backup_path == "@@@empty@@@":
        # We deleted a empty folder, recreate it
        path.mkdir()
    else:
        # Found a backup, restore it
        backup_path = Path(backup_path)
        if backup_path.exists():
            move_path(backup_path, path)
        else:
            # The backup does not exist, we can't restore it, ignore it
            pass
    # Remove the backup path from the config
    config.unset(key)

def download_file(url: str, path: Path) -> None:
    """Download a file from the given url to the given path
    """
    r = requests.get(url)
    r.raise_for_status()
    ensure_parent_exists(path)
    with path.open("wb") as f:
        f.write(r.content)

def main(dotfiles_dir: str, config_file: str) -> df.ui.DotfilesApp:
    """
    Main entry point for the this tool

    :param dotfiles_dir: The directory where the dotfiles are stored
    :param config_file: The path to the config file
    :return: The app object
    """

    # Save the dotfiles directory
    global DOTFILES_DIR
    DOTFILES_DIR = dotfiles_dir
    global DOTFILES_PATH
    DOTFILES_PATH = Path(dotfiles_dir)

    # Load the config file

    config = df.config.Config(config_file)

    # Start the GUI
    app = df.ui.DotfilesApp(config)
    app.run()
    return app
