import io
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "agent_skills"
NAME: str = "Agent Skills"
DESCRIPTION: str = "Links the Claude Code skills into ~/.agents/skills, where Codex and Copilot CLI read them"
DEPENDENCIES: List[str] = ["claude_config"]
CONFLICTING: List[str] = []

skills_path = Path.home() / ".agents" / "skills"


def skill_sources() -> List[Path]:
    return sorted(path for path in (df.DOTFILES_PATH / "claude" / "skills").iterdir() if path.is_dir())


def is_linked(source: Path) -> bool:
    target = skills_path / source.name
    return target.exists() and target.resolve() == source.resolve()


def link(source: Path, config: ModuleConfig) -> None:
    target = skills_path / source.name
    df.create_backup(target, config, f"old_skill_{source.name}")
    df.symlink_path(source, target)
    print(f"Linked {target}")


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source in skill_sources():
        link(source, config)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source in skill_sources():
        df.restore_backup(skills_path / source.name, config, f"old_skill_{source.name}")
        print(f"Restored {skills_path / source.name}")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return not all(is_linked(source) for source in skill_sources())


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source in skill_sources():
        if not is_linked(source):
            link(source, config)
