import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

DESK = Path(__file__).resolve().parents[1] / "desk"
sys.path.insert(0, str(DESK / "board"))
server = importlib.import_module("server")


class GoalTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        (self.home / "desk" / "backlog").mkdir(parents=True)

    def backlog(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": str(self.home)}
        return subprocess.run([sys.executable, str(DESK / "bin" / "backlog"), *args], env=env, capture_output=True, text=True)

    def test_an_item_joins_only_a_milestone_that_exists(self) -> None:
        self.backlog("goal", "new", "tea", "--title", "Tea", "--outcome", "Hot tea")
        self.backlog("goal", "milestone", "tea", "--title", "Heat", "--try", "Boil once")
        path = self.home / "desk" / "backlog" / "a.json"
        path.write_text(json.dumps({"id": "a", "title": "a", "status": "open", "comments": []}))
        self.assertNotEqual(self.backlog("goal", "attach", "a", "tea#2").returncode, 0)
        self.assertNotIn("parent", json.loads(path.read_text()))
        self.assertEqual(self.backlog("goal", "attach", "a", "tea#1").returncode, 0)
        self.assertEqual(json.loads(path.read_text())["parent"], "tea#1")

    def test_my_answer_minutes_count_toward_their_milestone(self) -> None:
        goals = self.home / "goals"
        goals.mkdir()
        milestones = [{"title": "one", "try": "x", "research": []}, {"title": "two", "try": "y", "research": []}]
        (goals / "tea.json").write_text(json.dumps({"slug": "tea", "milestones": milestones}))
        answered = [
            {"kind": "decide", "at": "2026-11-01T09:00:00", "opened": "2026-11-01T10:00:00", "answered": "2026-11-01T10:07:00"}
        ]
        items = [
            {"id": "a", "parent": "tea#2", "askLog": answered},
            {"id": "b", "parent": "other#2", "askLog": answered},
        ]
        with patch.object(server, "GOALS", goals):
            spent = [m["spent"] for m in server.load_goals(items)[0]["milestones"]]
        self.assertEqual(spent, [0, 7])


if __name__ == "__main__":
    unittest.main()
