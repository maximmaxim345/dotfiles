import io
import platform
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "sowershell_config"
NAME: str = "PowerShell Config"
DESCRIPTION: str = "A config for the PowerShell terminal emulator"
DEPENDENCIES: List[str] = ["starship_config"]
CONFLICTING: List[str] = []


def is_compatible() -> Union[bool, str]:
    return platform.system() == "Windows"


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "PowerShell"
    target_path = Path.home() / "Documents" / "WindowsPowerShell"

    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    target_path = Path.home() / "Documents" / "PowerShell"

    df.restore_backup(target_path, config, "old_path")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
