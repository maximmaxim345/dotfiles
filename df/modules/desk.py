import io
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
]


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin"]


def is_linked(source_name: str, target_name: str) -> bool:
    target_path = desk_path / target_name
    return target_path.is_symlink() and target_path.resolve() == (df.DOTFILES_PATH / "desk" / source_name).resolve()


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for name in DATA_DIRS:
        (desk_path / name).mkdir(parents=True, exist_ok=True)
    for source_name, target_name, key in ENTRIES:
        if is_linked(source_name, target_name):
            continue
        target_path = desk_path / target_name
        df.create_backup(target_path, config, key)
        df.symlink_path(df.DOTFILES_PATH / "desk" / source_name, target_path)
        print(f"Linked {target_path}", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for _, target_name, key in ENTRIES:
        df.restore_backup(desk_path / target_name, config, key)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    missing = [target for source, target, _ in ENTRIES if not is_linked(source, target)]
    return f"Missing links: {', '.join(missing)}" if missing else False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
