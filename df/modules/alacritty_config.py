import df
from df.config import ModuleConfig
import platform
from pathlib import Path
import io
from typing import Union, List

ID: str = "alacritty_config"
NAME: str = "Alacritty Config"
DESCRIPTION: str = "A config for the alacritty terminal emulator"
DEPENDENCIES: List[str] = ["fira_code_nerd_font"]
CONFLICTING: List[str] = []

def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "alacritty"
    target_path = Path.home() / ".config" / "alacritty"

    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    target_path = Path.home() / ".config" / "alacritty"
    df.restore_backup(target_path, config, "old_path")

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
