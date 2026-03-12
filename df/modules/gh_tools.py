import io
import shutil
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "gh_tools"
NAME: str = "GitHub Tools"
DESCRIPTION: str = "CLI tools for GitHub PRs (gh-pr-comments, gh-pr-info)"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

scripts = ["gh-pr-comments", "gh-pr-info"]
install_dir = Path.home() / ".local" / "bin"


def is_compatible() -> Union[bool, str]:
    if shutil.which("gh") is None:
        return "gh CLI is not installed"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_dir = df.DOTFILES_PATH / "gh-tools"
    for script in scripts:
        source = source_dir / script
        target = install_dir / script
        df.create_backup(target, config, f"old_{script}")
        df.symlink_path(source, target)
        print(f"Installed {script}")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for script in scripts:
        target = install_dir / script
        df.restore_backup(target, config, f"old_{script}")
        if df.delete_or_unlink(target):
            print(f"Removed {script}")
