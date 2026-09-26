import io
import json
from pathlib import Path
from typing import List, Optional, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "copilot_config"
NAME: str = "Copilot Config"
DESCRIPTION: str = "Global instructions and agents for GitHub Copilot CLI and the Copilot app, built from the Claude Code config"
DEPENDENCIES: List[str] = ["claude_config", "agent_skills"]
CONFLICTING: List[str] = []

copilot_path = Path.home() / ".copilot"
instructions_path = copilot_path / "instructions" / "global.instructions.md"
sage_path = copilot_path / "agents" / "ohf-sage.agent.md"
sage_source = Path.home() / ".claude" / "agents" / "ohf-sage.md"
implement_source = Path("copilot") / "agents" / "implement.agent.md"
implement_path = copilot_path / "agents" / "implement.agent.md"


def build_instructions() -> str:
    # Instruction files in this folder are path specific, so applyTo has to cover every file
    return '---\napplyTo: "**"\n---\n\n' + df.build_agent_instructions()


def build_sage() -> Optional[str]:
    if not sage_source.exists():
        return None
    fields, _ = df.read_frontmatter(sage_source.read_text(encoding="utf-8"))
    # Copilot caps an agent's instructions at 30,000 characters, so the agent loads the full file itself
    return (
        "---\n"
        f"name: {fields.get('name', 'ohf-sage')}\n"
        f"description: {json.dumps(fields.get('description', ''), ensure_ascii=False)}\n"
        "tools: [read, search]\n"
        "---\n\n"
        f"Read `{sage_source}` in full before anything else and follow it as your instructions, skipping its "
        "frontmatter. Where it names the Read, Grep and Glob tools, use your read and search tools.\n"
    )


def generated() -> List[Tuple[Path, Optional[str], str]]:
    """Each generated file with its expected content, None when it should not exist, and its backup key"""
    return [
        (instructions_path, build_instructions(), "old_global_instructions"),
        (sage_path, build_sage(), "old_ohf_sage"),
    ]


def is_current(path: Path, content: Optional[str]) -> bool:
    if content is None:
        return not path.exists()
    return path.is_file() and path.read_text(encoding="utf-8") == content


def write(path: Path, content: Optional[str]) -> None:
    if content is None:
        path.unlink(missing_ok=True)
        return
    df.ensure_parent_exists(path)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path}")


def is_implement_linked() -> bool:
    return implement_path.exists() and implement_path.resolve() == (df.DOTFILES_PATH / implement_source).resolve()


def link_implement(config: ModuleConfig) -> None:
    df.create_backup(implement_path, config, "old_implement_agent")
    df.symlink_path(df.DOTFILES_PATH / implement_source, implement_path)
    print(f"Linked {implement_path}")


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, content, key in generated():
        df.create_backup(path, config, key)
        write(path, content)
    link_implement(config)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, _, key in generated():
        # restore_backup only removes links and folders
        path.unlink(missing_ok=True)
        df.restore_backup(path, config, key)
    df.restore_backup(implement_path, config, "old_implement_agent")
    print("Copilot config removed")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return not is_implement_linked() or not all(is_current(path, content) for path, content, _ in generated())


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, content, _ in generated():
        if not is_current(path, content):
            write(path, content)
    if not is_implement_linked():
        link_implement(config)
