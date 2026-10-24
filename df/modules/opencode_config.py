import hashlib
import io
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import df
from df.config import ModuleConfig
from df.osinfo import running_in_termux, system

ID: str = "opencode_config"
NAME: str = "OpenCode Config"
DESCRIPTION: str = "Global instructions, commands and the OHF Sage agent for OpenCode, built from the Claude Code config"
DEPENDENCIES: List[str] = ["claude_config", "opencode"]
if system() == "Windows" or running_in_termux():
    DEPENDENCIES = ["claude_config"]  # The user has to install OpenCode manually there
CONFLICTING: List[str] = []

opencode_path = Path.home() / ".config" / "opencode"
instructions_path = opencode_path / "AGENTS.md"
sage_path = opencode_path / "agents" / "ohf-sage.md"
sage_source = Path.home() / ".claude" / "agents" / "ohf-sage.md"
commands_path = opencode_path / "commands"

COMMANDS = ("commit", "commit-split", "open-pr", "review-changes")
REFERENCE = re.compile(r"@?~/\.claude/([\w./-]+\.md)")

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


def render_command(name: str) -> str:
    pending = [f"skills/{name}/SKILL.md"]
    rendered: Dict[str, str] = {}
    for relative in pending:
        text = (df.DOTFILES_PATH / "claude" / relative).read_text(encoding="utf-8")
        if relative == pending[0]:
            fields, text = df.read_frontmatter(text)
            if "description" in fields:
                description = json.dumps(fields["description"], ensure_ascii=False)
                text = f"---\ndescription: {description}\n---\n{text}"
        text = re.sub(r" For the subagent variant use `/commit(?:-split)?-subagent`\.", "", text)
        text = re.sub(r"(?m)^The `commit-subagent` and `commit-split-subagent` skills delegate [^\n]*\n?", "", text)
        for match in REFERENCE.finditer(text):
            dependency = match.group(1)
            if dependency not in pending:
                pending.append(dependency)
        rendered[relative] = REFERENCE.sub(lambda match: match.group(1), text).rstrip()
    command = rendered.pop(pending[0])
    for relative, text in rendered.items():
        command += f'\n\n<included-file path="~/.claude/{relative}">\n\n{text}\n\n</included-file>'
    return command + "\n"


def remove_target(name: str, digest: Optional[str], config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    target = commands_path / f"{name}.md"
    if not target.exists() and not target.is_symlink():
        return
    if digest and not target.is_symlink() and target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == digest:
        target.unlink()
    else:
        key = f"old_{name}" if digest is None else f"edited_{name}"
        df.create_backup(target, config, key)
        print(f"Backed up {target} to {config.get(key)}", file=stdout)


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, content, key in generated():
        df.create_backup(path, config, key)
        write(path, content)
    update_commands(config, stdout)
    print("Restart OpenCode's background service to load it: opencode service restart")


def uninstall_commands(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    hashes = config.get("hashes", {})
    for name, digest in list(hashes.items()):
        target = commands_path / f"{name}.md"
        remove_target(name, digest, config, stdout)
        df.restore_backup(target, config, f"old_{name}")
        del hashes[name]
        config.set("hashes", hashes)
        print(f"Restored {target}", file=stdout)
    config.unset("hashes")


def commands_have_update(config: ModuleConfig) -> bool:
    hashes = config.get("hashes", {})
    for name in COMMANDS:
        digest = hashlib.sha256(render_command(name).encode("utf-8")).hexdigest()
        target = commands_path / f"{name}.md"
        if hashes.get(name) != digest or target.is_symlink() or not target.is_file():
            return True
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            return True
    return False


def update_commands(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    commands = {name: render_command(name) for name in COMMANDS}
    hashes = config.get("hashes", {})
    for name, text in commands.items():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        target = commands_path / f"{name}.md"
        if (
            hashes.get(name) == digest
            and not target.is_symlink()
            and target.is_file()
            and hashlib.sha256(target.read_bytes()).hexdigest() == digest
        ):
            continue
        remove_target(name, hashes.get(name), config, stdout)
        df.ensure_parent_exists(target)
        target.write_text(text, encoding="utf-8", newline="\n")
        hashes[name] = digest
        config.set("hashes", hashes)
        print(f"Wrote {target}", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for path, _, key in generated():
        path.unlink(missing_ok=True)
        df.restore_backup(path, config, key)
    uninstall_commands(config, stdout)
    print("OpenCode config removed")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return not all(is_current(path, content) for path, content, _ in generated()) or commands_have_update(config)


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    update_commands(config, stdout)
    for path, content, _ in generated():
        if not is_current(path, content):
            write(path, content)
