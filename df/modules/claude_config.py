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
    ("writing-examples.md", "writing-examples.md", "old_writing_examples"),
    ("commands", "commands", "old_commands"),
    ("output-styles", "output-styles", "old_output_styles"),
]


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def is_linked(source_name: str, target_name: str) -> bool:
    source_path = df.DOTFILES_PATH / "claude" / source_name
    target_path = claude_path / target_name
    return target_path.exists() and target_path.resolve() == source_path.resolve()


def link(source_name: str, target_name: str, key: str, config: ModuleConfig) -> None:
    source_path = df.DOTFILES_PATH / "claude" / source_name
    target_path = claude_path / target_name
    df.create_backup(target_path, config, key)
    df.symlink_path(source_path, target_path)
    print(f"Linked {target_path}")


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source_name, target_name, key in ENTRIES:
        link(source_name, target_name, key, config)
    print("Claude Code config installed, run /output-style Plain English once to select the output style")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for _, target_name, key in ENTRIES:
        df.restore_backup(claude_path / target_name, config, key)
        print(f"Restored {claude_path / target_name}")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return not all(is_linked(source_name, target_name) for source_name, target_name, _ in ENTRIES)


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source_name, target_name, key in ENTRIES:
        if not is_linked(source_name, target_name):
            link(source_name, target_name, key, config)
