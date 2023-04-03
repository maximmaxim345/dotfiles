from df.config import ModuleConfig
import platform
import tempfile
import subprocess
from pathlib import Path
import df
import io

ID: str = "picom_legacy_config"
NAME: str = "Picom Config for Legacy Systems"
DESCRIPTION: str = "Configures picom (jonaburg's fork) with animations and without modern features"
DEPENDENCIES: list[str] = []
CONFLICTING: list[str] = ["picom_config"]

config_path = Path.home() / ".config" / "picom.conf"

def is_compatible() -> bool | str:
    return platform.system() == "Linux"

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Symlink the config file
    source_path = df.DOTFILES_PATH / "picom-legacy.conf"
    df.create_backup(config_path, config, "old_path")
    df.symlink_path(source_path, config_path)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(config_path, config, "old_path")

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> bool | str:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
