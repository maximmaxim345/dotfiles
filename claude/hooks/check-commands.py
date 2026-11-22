#!/usr/bin/env python3
"""PreToolUse hook: block commands and GitHub posts that break a rule this hook can check exactly."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from typing import Iterator

DASHES = re.compile("[\u2013\u2014]")
AI_ATTRIBUTION = re.compile(
    r"^\s*co-authored-by:.*(claude|anthropic|copilot|codex|openai|chatgpt)"
    r"|generated (with|by)\W+(claude|copilot|codex|chatgpt)"
    r"|claude\.ai/code/session",
    re.IGNORECASE | re.MULTILINE,
)
COMMAND_START = r"(?:^|[;&|(\n])\s*(?:\w+=\S*\s+)*"
GIT_COMMIT = re.compile(COMMAND_START + r"git(?:\s+-[Cc]\s+\S+)*\s+commit\b")
FILE_FLAGS = ("--body-file", "-F", "--file", "--input")

DASH_REASON = (
    "Text for GitHub and commit messages must not contain em or en dashes. Use a comma, colon, parentheses or two "
    'sentences instead, and a hyphen or "to" for ranges. Found: {found}'
)
ATTRIBUTION_REASON = (
    'Remove the AI attribution (a co-author trailer, a "Generated with" line or a session link). Maxim\'s commits '
    "and PR text carry none."
)
CAFFEINATE_REASON = "Don't start caffeinate or keep the Mac awake."
EQUALS_REASON = "zsh reads an unquoted word that starts with = as a command name. Separate outputs with `echo ---`."


def runs(command: str, name: str) -> bool:
    return re.search(COMMAND_START + re.escape(name) + r"(?:\s|$)", command) is not None


def referenced_files(command: str, cwd: str) -> Iterator[str]:
    try:
        words = shlex.split(command, comments=False)
    except ValueError:
        return
    for index, flag in enumerate(words):
        if "=" in flag and flag.split("=", 1)[0] in FILE_FLAGS:
            value = flag.split("=", 1)[1]
        elif flag in FILE_FLAGS and index + 1 < len(words):
            value = words[index + 1]
        else:
            continue
        path = os.path.join(cwd, value.split("=@", 1)[-1].lstrip("@"))
        if value != "-" and os.path.isfile(path):
            with open(path, encoding="utf-8", errors="ignore") as f:
                yield f.read()


def strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def outgoing_text(tool: str, tool_input: dict, cwd: str) -> list[str]:
    if tool == "Bash":
        command = tool_input.get("command", "")
        if runs(command, "gh") or GIT_COMMIT.search(command):
            return [command, *referenced_files(command, cwd)]
        return []
    if tool.startswith("mcp__") and "github" in tool.lower():
        return list(strings(tool_input))
    return []


def problem(tool: str, tool_input: dict, cwd: str) -> str | None:
    for text in outgoing_text(tool, tool_input, cwd):
        dash = DASHES.search(text)
        if dash:
            return DASH_REASON.format(found=text[max(0, dash.start() - 30) : dash.end() + 30].strip())
        if AI_ATTRIBUTION.search(text):
            return ATTRIBUTION_REASON
    if tool != "Bash":
        return None
    command = tool_input.get("command", "")
    if runs(command, "caffeinate"):
        return CAFFEINATE_REASON
    if os.environ.get("SHELL", "").endswith("zsh") and re.search(COMMAND_START + r"echo\s+==", command):
        return EQUALS_REASON
    return None


def main() -> None:
    event = json.load(sys.stdin)
    reason = problem(event.get("tool_name", ""), event.get("tool_input") or {}, event.get("cwd") or os.getcwd())
    if reason:
        output = {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}
        print(json.dumps({"hookSpecificOutput": output}))


if __name__ == "__main__":
    main()
