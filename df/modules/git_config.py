import shutil
from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import io
from pathlib import Path
import df
from typing import Union, List

ID: str = "git_config"
NAME: str = "Git Config"
DESCRIPTION: str = "Basic git configuration, edit ~/.gitconfig to change name/email"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

target_path = Path.home() / ".gitconfig"
target_local_path = Path.home() / ".gitconfig.local"

def is_compatible() -> Union[bool, str]:
    # TODO: Add Windows support, symlinking the file won't work without admin permissions (or dev mode)
    return platform.system() in ["Linux", "Darwin"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "git/gitconfig"
    source_local_path = df.DOTFILES_PATH / "git/gitconfig.local"
    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)
    # Only create local config if it doesn't exist
    if not target_local_path.exists():
        # Copy, not symlink, so that we can edit it
        shutil.copyfile(source_local_path, target_local_path)
        print("Created local git config, edit ~/.gitconfig.local to change name/email")
    else:
        print("Local git config already exists, not overwriting")
        print(f"Look at {source_local_path} for an example")

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(target_path, config, "old_path")
    print("Keeping local git config (~/.gitconfig.local), you can delete it manually")

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
