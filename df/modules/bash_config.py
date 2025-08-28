import io
import platform
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "bash_config"
NAME: str = "Bash Config"
DESCRIPTION: str = "A simple bash config, incase zsh is not available"
DEPENDENCIES: List[str] = ["starship_config"]
CONFLICTING: List[str] = []

target_path = Path.home() / ".bashrc"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "bash/bashrc"
    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(target_path, config, "old_path")


# Optional functions for modules that can be updated


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
