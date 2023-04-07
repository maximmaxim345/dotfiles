from df.config import ModuleConfig
import platform
import tempfile
import subprocess
from pathlib import Path
import df
import io
from typing import Union, List

ID: str = "awesome_config"
NAME: str = "AwesomeWM config"
DESCRIPTION: str = "Configuration for AwesomeWM, this does not install awesome or required dependencies, see the README for more information."
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

def is_compatible() -> Union[bool, str]:
    return True

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "awesome"
    target_path = Path.home() / ".config" / "awesome"

    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    target_path = Path.home() / ".config" / "awesome"
    df.restore_backup(target_path, config, "old_path")

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
