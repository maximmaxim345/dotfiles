from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import io
from pathlib import Path
import df
from typing import Union, List

ID: str = "starship_config"
NAME: str = "Starship Config"
DESCRIPTION: str = "A rounded prompt for starship"
DEPENDENCIES: List[str] = ["starship"]
if platform.system() == "Windows":
    DEPENDENCIES = [] # The user has to manually install starship on Windows
CONFLICTING: List[str] = []

config_path = Path.home() / ".config" / "starship.toml"

def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin", "Windows"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Symlink the config file
    source_path = df.DOTFILES_PATH / "starship.toml"
    df.create_backup(config_path, config, "old_path")
    # TODO: On windows, we could also set the config via STARSHIP_CONFIG to avoid requiring higher permissions
    df.symlink_path(source_path, config_path)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(config_path, config, "old_path")

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
