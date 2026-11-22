#!/usr/bin/env python3
"""Stop hook: when a reply ends with a question but has no Ask line, have Claude add one."""

from __future__ import annotations

import json
import re
import sys

ASK = re.compile(r"^[\W_]*Ask\b")
REMINDER = (
    "Your reply ends with a question but has no Ask: line. Add one line that starts with Ask: and names the one "
    "thing you need from Maxim with your pick, and repeat nothing else."
)


def main() -> None:
    event = json.load(sys.stdin)
    if event.get("stop_hook_active"):
        return
    lines = [line.strip() for line in (event.get("last_assistant_message") or "").splitlines() if line.strip()]
    if any(ASK.match(line) for line in lines):
        return
    # Full URLs go below everything else, so the question sits above them.
    while lines and "://" in lines[-1]:
        lines.pop()
    if lines and lines[-1].rstrip("*_)\"'`").endswith("?"):
        print(json.dumps({"decision": "block", "reason": REMINDER}))


if __name__ == "__main__":
    main()
