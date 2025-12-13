import io
import platform
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "gw"
NAME: str = "gw (Git Worktree Tool)"
DESCRIPTION: str = "CLI tool for managing git worktrees"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

bin_path = Path.home() / ".local" / "bin" / "gw"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    script_path = df.DOTFILES_PATH / "gw.sh"

    # Ensure ~/.local/bin exists
    bin_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing if present
    if bin_path.exists() or bin_path.is_symlink():
        bin_path.unlink()

    # Create symlink
    df.symlink_path(script_path, bin_path)
    print(f"Symlinked {script_path} -> {bin_path}", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if bin_path.exists() or bin_path.is_symlink():
        bin_path.unlink()
        print(f"Removed {bin_path}", file=stdout)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
