import df
from df.config import ModuleConfig
import platform
from pathlib import Path
import io

ID: str = "kitty_config"
NAME: str = "Kitty Config"
DESCRIPTION: str = "A basic config for the kitty terminal emulator"
DEPENDENCIES: list[str] = ["fira_code_nerd_font"]
CONFLICTING: list[str] = []

def is_compatible() -> bool | str:
    return platform.system() in ["Linux", "Darwin"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "kitty"
    target_path = Path.home() / ".config" / "kitty"

    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    target_path = Path.home() / ".config" / "kitty"
    df.restore_backup(target_path, config, "old_path")

def has_update(config: ModuleConfig) -> bool | str:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
