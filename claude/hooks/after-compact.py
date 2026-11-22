#!/usr/bin/env python3
"""SessionStart hook: after a compaction, point Claude back at the files that hold the state of the work."""

from __future__ import annotations

import json
import sys

REMINDER = (
    "This thread was just compacted. Before you continue, read again the status or handoff file this work keeps, "
    "~/desk/TASK.md when this is a desk task, and ~/.claude/pr-followup.md when the work has a published PR."
)


def main() -> None:
    if json.load(sys.stdin).get("source") != "compact":
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": REMINDER}}))


if __name__ == "__main__":
    main()
