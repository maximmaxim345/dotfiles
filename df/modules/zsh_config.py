from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import shutil
import io
from pathlib import Path
import df
from typing import Union, List

ID: str = "zsh_config"
NAME: str = "Zsh Config"
DESCRIPTION: str = "A simple zsh config using zinit and starship"
DEPENDENCIES: List[str] = ["starship_config"]
CONFLICTING: List[str] = []

target_path = Path.home() / ".zshrc"
target_local_path = Path.home() / ".zshrc.local"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "zsh/zshrc"
    source_local_path = df.DOTFILES_PATH / "zsh/zshrc.local"
    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)
    # Only create local config if it doesn't exist
    if not target_local_path.exists():
        # Copy, not symlink, so that we can edit it
        shutil.copyfile(source_local_path, target_local_path)
        print("Created local zshrc config, edit ~/.zshrc.local to customize")
    else:
        print("Local zshrc config already exists, not overwriting")
        print(f"Look at {source_local_path} for an example")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(target_path, config, "old_path")
    print("Keeping local zshrc config (~/.zshrc.local), you can delete it manually")
    # We will leave the zinit directory for now


# Optional functions for modules that can be updated


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
