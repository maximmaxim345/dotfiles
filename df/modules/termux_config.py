import io
import os
import subprocess
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "termux_config"
NAME: str = "Termux config"
DESCRIPTION: str = "Configuration for termux on Android"
DEPENDENCIES: List[str] = ["fira_code_nerd_font"]
CONFLICTING: List[str] = []

target_path = Path.home() / ".termux/termux.properties"
target_path_font = Path.home() / ".termux/font.ttf"


def running_in_termux():
    prefix = os.environ.get("PREFIX")
    version = os.environ.get("TERMUX_VERSION")
    if prefix and version:
        return True
    else:
        return False


def is_compatible() -> Union[bool, str]:
    return running_in_termux()


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "termux/termux.properties"
    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)

    font_name = "Fira Code Medium Nerd Font Complete.ttf"
    fonts_folder = Path.home() / ".local/share/fonts/"
    source_path_font = fonts_folder / font_name
    df.create_backup(target_path_font, config, "old_path_font")
    df.symlink_path(source_path_font, target_path_font)

    print("Reloading settings...")
    try:
        subprocess.run(
            ["termux-reload-settings"],
            stdout=stdout,
            stderr=stdout,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("Error running termux-reload-settings")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(target_path, config, "old_path")
    df.restore_backup(target_path_font, config, "old_path_font")

    print("Reloading settings...")
    try:
        subprocess.run(
            ["termux-reload-settings"],
            stdout=stdout,
            stderr=stdout,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("Error running termux-reload-settings")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
