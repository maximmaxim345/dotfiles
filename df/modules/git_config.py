import shutil
from df.config import ModuleConfig
import platform
import io
from pathlib import Path
import df
from typing import Union, List

ID: str = "git_config"
NAME: str = "Git Config"
DESCRIPTION: str = "Basic git configuration template"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

target_path = Path.home() / ".gitconfig"


def is_compatible() -> Union[bool, str]:
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Check if already managed by dotfiles
    if target_path.exists():
        try:
            content = target_path.read_text()
            if "DOTFILES_MANAGED_GITCONFIG_MAXIMMAXIM345" in content:
                print("Git config already managed by dotfiles, skipping installation")
                return
        except (OSError, UnicodeDecodeError):
            pass  # If we can't read the file, proceed with installation

    source_path = df.DOTFILES_PATH / "git/gitconfig"
    df.create_backup(target_path, config, "old_path")
    shutil.copyfile(source_path, target_path)
    config.set("version", "1")
    print("Git config template created at ~/.gitconfig")
    print("Please configure your name, email, and other settings manually")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return config.get("version") != "1"


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    source_path = df.DOTFILES_PATH / "git/gitconfig"
    target_path.unlink(missing_ok=True)
    shutil.copyfile(source_path, target_path)
    config.set("version", "1")
    print("Git config template updated at ~/.gitconfig")
    print("Please update your name, email, and other settings manually")
    print(
        "You need to manually bring in your local git config (~/.gitconfig.local) if you want to keep those changes"
    )
