import io
import json
from pathlib import Path
from typing import List, Optional, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "codex_config"
NAME: str = "Codex Config"
DESCRIPTION: str = "Global instructions and the OHF Sage agent for the Codex CLI, built from the Claude Code config"
DEPENDENCIES: List[str] = ["claude_config", "agent_skills"]
CONFLICTING: List[str] = []

codex_path = Path.home() / ".codex"
instructions_path = codex_path / "AGENTS.md"
sage_path = codex_path / "agents" / "ohf-sage.toml"
sage_source = Path.home() / ".claude" / "agents" / "ohf-sage.md"


def build_sage() -> Optional[str]:
    if not sage_source.exists():
        return None
    fields, body = df.read_frontmatter(sage_source.read_text(encoding="utf-8"))
    # JSON strings are valid TOML basic strings
    return (
        f"name = {json.dumps(fields.get('name', 'ohf-sage'))}\n"
        f"description = {json.dumps(fields.get('description', ''), ensure_ascii=False)}\n"
        'sandbox_mode = "read-only"\n'
        f"developer_instructions = {json.dumps(body, ensure_ascii=False)}\n"
    )


def generated() -> List[Tuple[Path, Optional[str], str]]:
    """Each generated file with its expected content, None when it should not exist, and its backup key"""
    return [
        (instructions_path, df.build_agent_instructions(), "old_agents_md"),
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


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, content, key in generated():
        df.create_backup(path, config, key)
        write(path, content)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, _, key in generated():
        # restore_backup only removes links and folders
        path.unlink(missing_ok=True)
        df.restore_backup(path, config, key)
    print("Codex config removed")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return not all(is_current(path, content) for path, content, _ in generated())


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, content, _ in generated():
        if not is_current(path, content):
            write(path, content)
