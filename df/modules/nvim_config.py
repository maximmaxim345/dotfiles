from df.config import ModuleConfig
import platform
import tempfile
import subprocess
from pathlib import Path
import df
import io
from typing import Union, List

ID: str = "nvim_config"
NAME: str = "(old) Neovim config"
DESCRIPTION: str = "A config for neovim, use the Lazyvim based config instead"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = ["nvim_config_lazyvim"]


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Windows", "Darwin", "Linux"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "nvim"
    target_path = Path.home() / ".config" / "nvim"

    if platform.system() == "Windows":
        # On Windows, use the AppData directory for the config
        target_path = Path.home() / "AppData" / "Local" / "nvim"

    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    target_path = Path.home() / ".config" / "nvim"

    if platform.system() == "Windows":
        target_path = Path.home() / "AppData" / "Local" / "nvim"

    df.restore_backup(target_path, config, "old_path")


# Optional functions for modules that can be updated


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
