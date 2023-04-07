from df.config import ModuleConfig
import platform
import tempfile
import subprocess
from pathlib import Path
import df
import io
from typing import Union, List

ID: str = "xresources_config"
NAME: str = "Xresources Config"
DESCRIPTION: str = "Basic Xresources configuration for Xterm and URxvt"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

def is_compatible() -> Union[bool, str]:
    return platform.system() == "Linux"

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    config_path = Path.home() / ".Xresources"
    source_path = df.DOTFILES_PATH / "Xresources"
    df.create_backup(config_path, config, "old_path")
    df.symlink_path(source_path, config_path)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    config_path = Path.home() / ".Xresources"
    df.restore_backup(config_path, config, "old_path")

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
