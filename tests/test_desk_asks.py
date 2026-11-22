import importlib
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desk" / "board"))
server = importlib.import_module("server")


class AskLogTests(unittest.TestCase):
    def test_status_change_keeps_the_cleared_question_with_its_kind(self) -> None:
        item: dict[str, Any] = {"status": "started", "asks": {"text": "Push?", "at": "2026-11-20T10:00:00+01:00", "kind": "push"}}
        item["answer"] = {"text": "go", "to": "Push?", "at": "2026-11-20T12:00:00+01:00"}
        server.apply_status(item, "done")
        self.assertNotIn("asks", item)
        [entry] = item["askLog"]
        self.assertEqual(
            {k: entry[k] for k in ("kind", "asked", "answered")},
            {"kind": "push", "asked": "2026-11-20T10:00:00+01:00", "answered": "2026-11-20T12:00:00+01:00"},
        )
        self.assertTrue(entry["cleared"])


if __name__ == "__main__":
    unittest.main()
