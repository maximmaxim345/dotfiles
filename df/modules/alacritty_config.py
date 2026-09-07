import io
import os
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "alacritty_config"
NAME: str = "Alacritty Config"
DESCRIPTION: str = "A config for the alacritty terminal emulator"
DEPENDENCIES: List[str] = ["fira_code_nerd_font"]
CONFLICTING: List[str] = []


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "alacritty"
    if system() == "Windows":
        target_path = Path(os.path.expandvars("%APPDATA%")) / "alacritty"
    else:
        target_path = Path.home() / ".config" / "alacritty"

    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if system() == "Windows":
        target_path = Path(os.path.expandvars("%APPDATA%")) / "alacritty"
    else:
        target_path = Path.home() / ".config" / "alacritty"

    df.restore_backup(target_path, config, "old_path")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
