#!/usr/bin/env python3
"""UserPromptSubmit hook: remind Claude to open with a recap when the thread was quiet for an hour or more."""

from __future__ import annotations

import datetime
import json
import os
import sys

BREAK = datetime.timedelta(hours=1)
TAIL_BYTES = 1 << 20
REMINDER = (
    "This thread was quiet for {gap} before this message. When it comes from Maxim, not from another thread, "
    "open your reply with two lines before anything else: what this thread works on and why, then where it "
    "stands and what waits on him."
)


def last_reply(path: str) -> datetime.datetime | None:
    with open(path, "rb") as f:
        f.seek(max(0, os.path.getsize(path) - TAIL_BYTES))
        lines = f.read().decode(errors="ignore").splitlines()
    for line in reversed(lines):
        if '"type":"assistant"' not in line.replace(" ", ""):
            continue
        try:
            stamp = json.loads(line).get("timestamp")
        except json.JSONDecodeError:
            continue
        if stamp:
            return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return None


def main() -> None:
    event = json.load(sys.stdin)
    path = event.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    last = last_reply(path)
    if last is None:
        return
    gap = datetime.datetime.now(datetime.timezone.utc) - last
    if gap < BREAK:
        return
    hours = gap.total_seconds() / 3600
    text = REMINDER.format(gap=f"{hours:.0f} hours" if hours >= 2 else "over an hour")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))


if __name__ == "__main__":
    main()
