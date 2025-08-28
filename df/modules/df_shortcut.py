import io
import platform
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "df_shortcut"
NAME: str = "Dotfiles Manager Shortcut"
DESCRIPTION: str = "Shortcut to launch this dotfiles manager"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []


def is_compatible() -> Union[bool, str]:
    # Only compatible with Linux
    return platform.system() == "Linux"


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Create the desktop file
    desktop = f"""[Desktop Entry]
Type=Application
Name=Dotfiles Manger
Comment=Install/Uninstall dotfiles
Exec=python3 {df.DOTFILES_PATH / "dotfiles.py"}
Terminal=true
Categories=DesktopSettings;Settings;"""
    # Write the desktop file (create the directory if it doesn't exist)
    (Path.home() / ".local" / "share" / "applications").mkdir(
        parents=True, exist_ok=True
    )
    with open(
        Path.home() / ".local" / "share" / "applications" / "dotfiles.desktop", "w"
    ) as f:
        f.write(desktop)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Just remove the desktop file
    (Path.home() / ".local" / "share" / "applications" / "dotfiles.desktop").unlink(
        missing_ok=True
    )


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
