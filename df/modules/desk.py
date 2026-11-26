import io
import os
from pathlib import Path
from typing import List, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "desk"
NAME: str = "Desk"
DESCRIPTION: str = "Link the desk's rules, scripts and board into ~/desk, which keeps the backlog and efforts"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

desk_path = Path.home() / "desk"
DATA_DIRS: List[str] = ["backlog", "efforts", "state"]

# (source relative to desk/, target relative to ~/desk, config key for the backup)
ENTRIES: List[Tuple[str, str, str]] = [
    ("AGENTS.md", "AGENTS.md", "old_agents_md"),
    ("AGENTS.md", "CLAUDE.md", "old_claude_md"),
    ("TASK.md", "TASK.md", "old_task_md"),
    ("bin", "bin", "old_bin"),
    ("board", "board", "old_board"),
    ("rules", "rules", "old_rules"),
]


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin"]


# The links are relative, since ~/desk is synced to machines with another home folder.
def link_text(source_name: str) -> str:
    return os.path.relpath(df.DOTFILES_PATH / "desk" / source_name, desk_path)


def is_linked(source_name: str, target_name: str) -> bool:
    target_path = desk_path / target_name
    return target_path.is_symlink() and os.readlink(target_path) == link_text(source_name)


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for name in DATA_DIRS:
        (desk_path / name).mkdir(parents=True, exist_ok=True)
    for source_name, target_name, key in ENTRIES:
        if is_linked(source_name, target_name):
            continue
        target_path = desk_path / target_name
        source_path = df.DOTFILES_PATH / "desk" / source_name
        if target_path.is_symlink() and target_path.resolve() == source_path.resolve():
            target_path.unlink()
        else:
            df.create_backup(target_path, config, key)
        target_path.symlink_to(link_text(source_name))
        print(f"Linked {target_path}", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for _, target_name, key in ENTRIES:
        df.restore_backup(desk_path / target_name, config, key)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    missing = [target for source, target, _ in ENTRIES if not is_linked(source, target)]
    return f"Links to update: {', '.join(missing)}" if missing else False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
