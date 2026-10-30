import io
import json
from pathlib import Path
from typing import List, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "claude_config"
NAME: str = "Claude Code Config"
DESCRIPTION: str = "Global instructions, guidelines, skills and output style for Claude Code"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

claude_path = Path.home() / ".claude"
settings_path = claude_path / "settings.json"
desk_path = Path.home() / "desk"
# Account folders of cswap, each used as CLAUDE_CONFIG_DIR
accounts_path = Path.home() / ".claude-swap-backup" / "sessions"
# What Claude Code reads from its config folder, linked from ~/.claude into each account folder
ACCOUNT_ENTRIES: List[str] = ["CLAUDE.md", "output-styles", "skills", "agents", "settings.json"]

# (source relative to claude/, target relative to ~/.claude, config key for the backup)
ENTRIES: List[Tuple[str, str, str]] = [
    ("CLAUDE.md", "CLAUDE.md", "old_claude_md"),
    ("commit-guidelines.md", "commit-guidelines.md", "old_commit_guidelines"),
    ("pr-guidelines.md", "pr-guidelines.md", "old_pr_guidelines"),
    ("writing-examples.md", "writing-examples.md", "old_writing_examples"),
    ("pr-followup.md", "pr-followup.md", "old_pr_followup"),
    ("output-styles", "output-styles", "old_output_styles"),
    ("project-rules", "project-rules", "old_project_rules"),
    ("skills/implement", "skills/implement", "old_skill_implement"),
    ("skills/review-brief", "skills/review-brief", "old_skill_review_brief"),
    ("skills/blast-radius", "skills/blast-radius", "old_skill_blast_radius"),
    ("skills/ma-dev", "skills/ma-dev", "old_skill_ma_dev"),
    ("skills/manager", "skills/manager", "old_skill_manager"),
    ("skills/ma-device-test", "skills/ma-device-test", "old_skill_ma_device_test"),
    ("skills/open-pr", "skills/open-pr", "old_skill_open_pr"),
    ("skills/review-changes", "skills/review-changes", "old_skill_review_changes"),
    ("skills/desk", "skills/desk", "old_skill_desk"),
    ("skills/babysit", "skills/babysit", "old_skill_babysit"),
]
# Entries dropped from ENTRIES, whose links existing installs still have (target, config key for the backup)
REMOVED: List[Tuple[str, str]] = [
    ("commit-subagent-prompt.md", "old_commit_subagent_prompt"),
    ("commands", "old_commands"),
    ("skills/commit", "old_skill_commit"),
    ("skills/commit-split", "old_skill_commit_split"),
    ("mods", "old_mods"),
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


def missing_account_links() -> List[Tuple[Path, Path]]:
    if not accounts_path.is_dir():
        return []
    return [
        (claude_path / name, account / name)
        for account in sorted(accounts_path.iterdir())
        if account.is_dir()
        for name in ACCOUNT_ENTRIES
        if (claude_path / name).exists() and not (account / name).exists() and not (account / name).is_symlink()
    ]


def removed_links() -> List[Tuple[Path, str]]:
    return [
        (claude_path / target, key)
        for target, key in REMOVED
        if (claude_path / target).is_symlink()
        and (claude_path / target).resolve() == (df.DOTFILES_PATH / "claude" / target).resolve()
    ]


def dangling_account_links(config: ModuleConfig) -> List[Path]:
    return [Path(target) for target in config.get("account_links", []) if Path(target).is_symlink() and not Path(target).exists()]


def unlink_removed(config: ModuleConfig) -> None:
    for target, key in removed_links():
        df.restore_backup(target, config, key)
        print(f"Restored {target}")
    created = config.get("account_links", [])
    for target in dangling_account_links(config):
        df.delete_or_unlink(target)
        created.remove(str(target))
        print(f"Removed {target}")
    config.set("account_links", created)


def link_accounts(config: ModuleConfig) -> None:
    created = config.get("account_links", [])
    for source, target in missing_account_links():
        df.symlink_path(source, target)
        created.append(str(target))
        print(f"Linked {target}")
    config.set("account_links", created)


def missing_desk_dirs() -> List[str]:
    if not desk_path.is_dir() or not settings_path.is_file():
        return []
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    allowed = settings.get("permissions", {}).get("additionalDirectories", [])
    # Reads through the links in ~/desk also need their dotfiles targets allowed
    return [str(path) for path in (desk_path, df.DOTFILES_PATH / "desk") if str(path) not in allowed]


def allow_desk(config: ModuleConfig) -> None:
    missing = missing_desk_dirs()
    if not missing:
        return
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings.setdefault("permissions", {}).setdefault("additionalDirectories", []).extend(missing)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    config.set("allowed_desk", True)
    print(f"Allowed {', '.join(missing)} in {settings_path}")


def disallow_desk(config: ModuleConfig) -> None:
    if not config.get("allowed_desk", False) or not settings_path.is_file():
        return
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    allowed = settings.get("permissions", {}).get("additionalDirectories", [])
    added = [path for path in (str(desk_path), str(df.DOTFILES_PATH / "desk")) if path in allowed]
    for path in added:
        allowed.remove(path)
    if added:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    config.unset("allowed_desk")


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for source_name, target_name, key in ENTRIES:
        link(source_name, target_name, key, config)
    link_accounts(config)
    allow_desk(config)
    print("Claude Code config installed, run /output-style Plain English once to select the output style")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    disallow_desk(config)
    unlink_removed(config)
    for _, target_name, key in ENTRIES:
        df.restore_backup(claude_path / target_name, config, key)
        print(f"Restored {claude_path / target_name}")
    for target in config.get("account_links", []):
        df.delete_or_unlink(Path(target))
    config.unset("account_links")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    linked = all(is_linked(source_name, target_name) for source_name, target_name, _ in ENTRIES)
    return (
        not linked
        or bool(removed_links())
        or bool(dangling_account_links(config))
        or bool(missing_account_links())
        or bool(missing_desk_dirs())
    )


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    unlink_removed(config)
    for source_name, target_name, key in ENTRIES:
        if not is_linked(source_name, target_name):
            link(source_name, target_name, key, config)
    link_accounts(config)
    allow_desk(config)
