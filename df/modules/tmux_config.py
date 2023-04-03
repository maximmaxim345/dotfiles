from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import shutil
from pathlib import Path
import df
import io

ID: str = "tmux_config"
NAME: str = "Tmux config"
DESCRIPTION: str = "Configuration for tmux based on oh-my-tmux"
DEPENDENCIES: list[str] = []
CONFLICTING: list[str] = []

target_path = Path.home() / ".tmux.conf"
target_local_path = Path.home() / ".tmux.conf.local"

def is_compatible() -> bool | str:
    return platform.system() in ("Linux", "Darwin")

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "tmux/oh-my-tmux/.tmux.conf"
    source_local_path = df.DOTFILES_PATH / "tmux/.tmux.conf.local"
    df.create_backup(target_path, config, "old_path")
    df.symlink_path(source_path, target_path)
    # Only create local config if it doesn't exist
    if not target_local_path.exists():
        # Copy, not symlink, so that we can edit it
        shutil.copyfile(source_local_path, target_local_path)
        print("Created local tmux config, edit ~/.tmux.conf.local to customize")
    else:
        print("Local tmux config already exists, not overwriting")
        print(f"Look at {source_local_path} for an example")

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.restore_backup(target_path, config, "old_path")
    print("Keeping local tmux config (~/.tmux.conf.local), you can delete it manually")

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> bool | str:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
