import contextlib
import datetime
import importlib.machinery
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "desk" / "bin" / "autostart"
loader = importlib.machinery.SourceFileLoader("autostart", str(SCRIPT))
spec = importlib.util.spec_from_loader("autostart", loader)
assert spec
autostart = importlib.util.module_from_spec(spec)
loader.exec_module(autostart)

BRIEF = "## Goal\n\nx\n\n## Done when\n\nx\n\n## Plan\n\nx\n\n## Drop if\n\nx\n"


def item(item_id: str, kind: str = "feature", status: str = "open", **fields: object) -> dict:
    created = datetime.date.today().isoformat()
    return {
        "id": item_id,
        "title": item_id,
        "kind": kind,
        "status": status,
        "brief": BRIEF,
        "created": created,
        "comments": [],
        **fields,
    }


class AutostartTests(unittest.TestCase):
    def test_reviews_that_wait_on_me_hold_the_next_review_but_not_work(self) -> None:
        asks = {"text": "post these?", "at": "2026-11-23T10:00:00+01:00", "kind": "review"}
        items = {
            "review-1": item("review-1", "review", "started", thread="t1", asks=asks, firstPass=True),
            "review-2": item("review-2", "review", "started", thread="t2", asks=asks, firstPass=True),
            "review-3": item("review-3", "review", "started", thread="t3", asks=asks, firstPass=True),
            "review-4": item("review-4", "review", firstPass=True),
            "work": item("work", suggested="soon"),
        }
        missing = Path(__file__).parent / "no-such-file.json"
        out = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.multiple(
                autostart,
                THREADS=missing,
                INCOMING=missing,
                WORKTREES=missing,
                AUTOSTART_LAST=Path(folder) / "autostart-last.json",
                all_items=lambda: items,
                autostart_setting=lambda: {"mode": "all", "efforts": [], "reviews": True},
                spaces_setting=lambda: {"spaces": ["work"], "off": [], "efforts": {}},
                plan_day=lambda *args: {"moves": {}, "rows": [{"id": "review-4", "today": True}]},
                in_window=lambda now: True,
            ),
            contextlib.redirect_stdout(out),
        ):
            autostart.main()
        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].endswith("Held: 1 item because 2 reviews run or wait on me"), lines[0])
        self.assertEqual(lines[1:], ["start work"])


if __name__ == "__main__":
    unittest.main()
