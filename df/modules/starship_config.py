import io
import platform
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "starship_config"
NAME: str = "Starship Config"
DESCRIPTION: str = "A rounded prompt for starship"
DEPENDENCIES: List[str] = ["starship"]
if platform.system() == "Windows":
    DEPENDENCIES = []  # The user has to manually install starship on Windows
CONFLICTING: List[str] = []

config_path = Path.home() / ".config" / "starship.toml"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "starship.toml"
    if platform.system() == "Windows":
        # Windows requires higher permissions to symlink files, so we'll set a system environment variable instead
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            old_value, _ = winreg.QueryValueEx(key, "STARSHIP_CONFIG")
            config.set("old_starship_config", old_value)
        except FileNotFoundError:
            pass
        winreg.SetValueEx(key, "STARSHIP_CONFIG", 0, winreg.REG_SZ, str(source_path))
        winreg.CloseKey(key)
    else:
        # Symlink the config file
        df.create_backup(config_path, config, "old_path")
        df.symlink_path(source_path, config_path)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if platform.system() == "Windows":
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        old_value = config.get("old_starship_config", None)
        if old_value is not None:
            winreg.SetValueEx(key, "STARSHIP_CONFIG", 0, winreg.REG_SZ, old_value)
            config.unset("old_starship_config")
        else:
            winreg.DeleteValue(key, "STARSHIP_CONFIG")
        winreg.CloseKey(key)
    else:
        df.restore_backup(config_path, config, "old_path")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
