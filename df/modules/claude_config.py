import io
from pathlib import Path
from typing import List, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "claude_config"
NAME: str = "Claude Code Config"
DESCRIPTION: str = "Global instructions, guidelines, slash commands and output style for Claude Code"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

claude_path = Path.home() / ".claude"

# (source relative to claude/, target relative to ~/.claude, config key for the backup)
ENTRIES: List[Tuple[str, str, str]] = [
    ("CLAUDE.md", "CLAUDE.md", "old_claude_md"),
    ("prompts.md", "prompts.md", "old_prompts"),
    ("commit-guidelines.md", "commit-guidelines.md", "old_commit_guidelines"),
    ("pr-guidelines.md", "pr-guidelines.md", "old_pr_guidelines"),
    ("commit-subagent-prompt.md", "commit-subagent-prompt.md", "old_commit_subagent_prompt"),
    ("commands", "commands", "old_commands"),
    ("output-styles", "output-styles", "old_output_styles"),
]


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source_name, target_name, key in ENTRIES:
        source_path = df.DOTFILES_PATH / "claude" / source_name
        target_path = claude_path / target_name
        df.create_backup(target_path, config, key)
        df.symlink_path(source_path, target_path)
        print(f"Linked {target_path}")
    print("Claude Code config installed, run /output-style Plain English once to select the output style")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for _, target_name, key in ENTRIES:
        df.restore_backup(claude_path / target_name, config, key)
        print(f"Restored {claude_path / target_name}")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
