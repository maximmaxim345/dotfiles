import io
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "opencode_config"
NAME: str = "OpenCode Config"
DESCRIPTION: str = "Global instructions and the OHF Sage agent for OpenCode, built from the Claude Code config"
DEPENDENCIES: List[str] = ["claude_config", "opencode"]
CONFLICTING: List[str] = []

opencode_path = Path.home() / ".config" / "opencode"
instructions_path = opencode_path / "AGENTS.md"
sage_path = opencode_path / "agents" / "ohf-sage.md"
sage_source = Path.home() / ".claude" / "agents" / "ohf-sage.md"

# Blocks other tools write into AGENTS.md, like codebase-memory-mcp
MARKER_BLOCK = re.compile(r"<!-- ([\w.-]+):start -->.*?<!-- \1:end -->\n?", re.S)


def build_instructions() -> str:
    existing = instructions_path.read_text(encoding="utf-8") if instructions_path.is_file() else ""
    kept = "".join("\n" + block.group(0).rstrip("\n") + "\n" for block in MARKER_BLOCK.finditer(existing))
    return df.build_agent_instructions() + kept


def build_sage() -> Optional[str]:
    if not sage_source.exists():
        return None
    fields, body = df.read_frontmatter(sage_source.read_text(encoding="utf-8"))
    # JSON strings are valid YAML double-quoted strings
    description = json.dumps(fields.get("description", ""), ensure_ascii=False)
    return f"---\ndescription: {description}\nmode: subagent\npermission:\n  edit: deny\n  bash: deny\n---\n{body}"


def generated() -> List[Tuple[Path, Optional[str], str]]:
    return [
        (instructions_path, build_instructions(), "old_agents_md"),
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
    print("Restart OpenCode's background service to load it: opencode service restart")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, _, key in generated():
        path.unlink(missing_ok=True)
        df.restore_backup(path, config, key)
    print("OpenCode config removed")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return not all(is_current(path, content) for path, content, _ in generated())


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, content, _ in generated():
        if not is_current(path, content):
            write(path, content)
