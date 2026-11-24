#!/usr/bin/env python3
"""Print the lines of a commit, or of a range A..B, that git does not count as part of a moved block."""

import re
import subprocess
import sys

COLORS = {
    "old": "red",
    "new": "green",
    "oldMoved": "magenta",
    "oldMovedAlternative": "magenta",
    "newMoved": "cyan",
    "newMovedAlternative": "blue",
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


root = git("rev-parse", "--show-toplevel").strip()
settings = [arg for name, color in COLORS.items() for arg in ("-c", f"color.diff.{name}={color}")]
diff = git(
    *settings,
    *(["diff"] if ".." in sys.argv[1] else ["show", "--format="]),
    "-U0",
    "--no-ext-diff",
    "--color=always",
    "--color-moved=zebra",
    "--color-moved-ws=allow-indentation-change",
    "--src-prefix=a/",
    "--dst-prefix=b/",
    sys.argv[1],
)
old_path = new_path = ""
old_line = new_line = old_left = new_left = 0
last_moved = (-1, "")
for raw in diff.splitlines():
    code = re.match(r"\x1b\[(\d+)m", raw)
    line = re.sub(r"\x1b\[[\d;]*m", "", raw)
    hunk = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if hunk:
        old_line, new_line = int(hunk[1]), int(hunk[3])
        old_left, new_left = int(hunk[2] or 1), int(hunk[4] or 1)
    elif line.startswith("-") and old_left:
        if line[1:].strip() and code and code[1] == "31":
            print(f"- {root}/{old_path}:{old_line} (before) {line[1:].strip()}")
        old_line, old_left = old_line + 1, old_left - 1
    elif line.startswith("+") and new_left:
        if line[1:].strip() and code and code[1] == "32":
            print(f"+ {root}/{new_path}:{new_line} {line[1:].strip()}")
        elif code and code[1] in ("34", "36"):
            if last_moved[0] == new_line - 1 and last_moved[1] != code[1]:
                print(f"~ {root}/{new_path}:{new_line} another moved block starts here")
            last_moved = (new_line, code[1])
        new_line, new_left = new_line + 1, new_left - 1
    elif line.startswith("--- a/"):
        old_path = line[6:]
    elif line.startswith("+++ b/"):
        new_path, last_moved = line[6:], (-1, "")
