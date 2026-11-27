import datetime
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
SPACES = {"spaces": ["work"], "off": [], "efforts": {}}


def item(item_id: str, minutes: int = 20, **fields: object) -> dict:
    return {
        "id": item_id,
        "title": item_id,
        "status": "open",
        "created": datetime.date.today().isoformat(),
        "minutes": minutes,
        "comments": [],
        **fields,
    }


class TodayRowsTests(unittest.TestCase):
    def rows(self, items: list[dict], moves: dict[str, str], budget: int, waiting: int = 0) -> dict[str, bool]:
        by_id = {i["id"]: i for i in items}
        return {row["id"]: row["today"] for row in server.today_rows(by_id, {"moves": moves}, budget, waiting, SPACES)}

    def test_the_line_falls_where_the_minutes_run_out_and_stays_there(self) -> None:
        items = [item("a", 30), item("b", 30), item("c", 5)]
        self.assertEqual(self.rows(items, {}, 60, waiting=10), {"a": True, "b": False, "c": False})

    def test_my_moves_and_urgent_items_take_the_budget_first(self) -> None:
        items = [item("a", 30), item("b", 30), item("c", 30, urgent=True), item("d", 30)]
        self.assertEqual(self.rows(items, {"a": "later", "d": "today"}, 60), {"a": False, "b": False, "c": True, "d": True})


class AskMinutesTests(unittest.TestCase):
    def log(self, minutes: float, opened: bool = True) -> dict:
        start = datetime.datetime(2026, 11, 20, 10, tzinfo=datetime.timezone.utc)
        end = start + datetime.timedelta(minutes=minutes)
        return {
            "kind": "review",
            "asked": start.isoformat(),
            "opened": start.isoformat() if opened else None,
            "answered": end.isoformat(),
        }

    def test_estimate_switches_to_my_median_once_enough_samples_exist(self) -> None:
        few = [self.log(m) for m in (8, 9, 10, 11)] + [self.log(500), self.log(3, opened=False)]
        self.assertEqual(server.ask_minutes([{"askLog": few}])["review"]["minutes"], 20)
        enough = few + [self.log(12)]
        self.assertEqual(server.ask_minutes([{"askLog": enough}])["review"]["minutes"], 10)


class TodayPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        for name, path in (("BACKLOG", self.folder), ("STATE", self.folder), ("TODAY", self.folder / "today.json")):
            patcher = patch.object(server, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_my_next_column_moves_onto_today_in_its_order(self) -> None:
        items = {"b": item("b", status="next", rank=2), "a": item("a", status="next", rank=1), "c": item("c")}
        for entry in items.values():
            (self.folder / f"{entry['id']}.json").write_text(json.dumps(entry))
        plan = server.today_plan(items)
        saved = json.loads((self.folder / "b.json").read_text())
        self.assertEqual(list(plan["moves"].items()), [("a", "today"), ("b", "today")])
        self.assertEqual((saved["status"], "rank" in saved, saved["comments"][0]["by"]), ("open", False, "desk"))

    def test_an_item_marked_urgent_after_the_plan_was_made_reaches_today(self) -> None:
        items = {"a": item("a", 30)}
        server.today_plan(items)
        items["b"] = item("b", 30, urgent=True)
        rows = server.today_rows(items, server.today_plan(items), 30, 0, SPACES)
        self.assertEqual({row["id"]: row["today"] for row in rows}, {"b": True, "a": False})


class AutostartTodayTests(unittest.TestCase):
    def test_auto_start_starts_today_above_the_line_and_skips_rows_i_moved_later(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            desk = Path(home) / "desk"
            (desk / "backlog").mkdir(parents=True)
            (desk / "state").mkdir()
            (Path(home) / ".config" / "desk").mkdir(parents=True)
            (Path(home) / ".config" / "desk" / "home").touch()
            (desk / "state" / "autostart.json").write_text(json.dumps({"mode": "all", "efforts": [], "reviews": False}))
            (desk / "state" / "budget.json").write_text(json.dumps({"minutes": 30}))
            day = datetime.date.today().isoformat()
            (desk / "state" / "today.json").write_text(json.dumps({"date": day, "moves": {"pick": "later"}}))
            brief = "## Goal\nx\n## Done when\nx\n## Plan\nx"
            for entry in (item("fits", 20), item("long", 40), item("pick", 10, suggested="soon")):
                (desk / "backlog" / f"{entry['id']}.json").write_text(json.dumps({**entry, "brief": brief}))
            run = (
                "import importlib.machinery, importlib.util, sys\n"
                "loader = importlib.machinery.SourceFileLoader('autostart', sys.argv[1])\n"
                "module = importlib.util.module_from_spec(importlib.util.spec_from_loader('autostart', loader))\n"
                "loader.exec_module(module)\n"
                "module.in_window = lambda now: True\n"
                "module.main()\n"
            )
            result = subprocess.run(
                [sys.executable, "-c", run, str(DESK / "bin" / "autostart")],
                env={**os.environ, "HOME": home},
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[1:], ["start fits"])


class ParkedTests(unittest.TestCase):
    def test_items_nobody_touched_for_two_weeks_stay_off_today(self) -> None:
        old = (datetime.date.today() - datetime.timedelta(days=15)).isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        items = {
            "idle": item("idle", created=old),
            "commented": item("commented", created=old, comments=[{"at": f"{yesterday}T10:00:00", "by": "me", "text": "x"}]),
            "kept": item("kept", created=old, kept=f"{yesterday}T10:00:00"),
        }
        self.assertEqual([row["id"] for row in server.today_rows(items, {"moves": {}}, 240, 0, SPACES)], ["commented", "kept"])

    def test_an_item_whose_blocker_just_finished_is_not_parked(self) -> None:
        old = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        items = {"waits": item("waits", created=old, blockedBy=["first"]), "first": item("first", status="done", done=yesterday)}
        self.assertFalse(server.parked(items["waits"], items))


class NowRowsTests(unittest.TestCase):
    def test_someone_waiting_comes_first_then_quick_questions(self) -> None:
        asks = {"kind": "review", "text": "Review?", "at": "2026-11-20T10:00:00+00:00"}
        items = {
            "review": item("review", status="started", thread="t1", asks=asks),
            "push": item("push", status="started", thread="t2", asks={**asks, "kind": "push", "text": "Push?"}),
        }
        incoming = [{"url": "u", "title": "issue", "status": "needs-you", "updated": "2026-11-21T10:00:00Z"}]
        rows = server.now_rows(items, {}, incoming, None, {}, SPACES)
        self.assertEqual([row["kind"] for row in rows], ["reply", "push", "review"])

    def test_rows_go_to_the_first_group_that_fits_before_quicker_rows_of_later_groups(self) -> None:
        asks = {"kind": "review", "text": "Review?", "at": "2026-11-20T10:00:00+00:00"}
        items = {
            "urgent": item("urgent", status="started", thread="t1", urgent=True, asks=asks),
            "push": item("push", status="started", thread="t2", asks={**asks, "kind": "push"}),
            "question": item("question", status="started", thread="t3", asks={**asks, "kind": "question", "minutes": 1}),
        }
        incoming = [{"url": "u", "title": "issue", "status": "needs-you", "updated": "2026-11-21T10:00:00Z"}]
        rows = server.now_rows(items, {}, incoming, None, {}, SPACES)
        self.assertEqual(
            [(row["kind"], row["group"]) for row in rows],
            [("review", "act"), ("reply", "unblock"), ("push", "land"), ("question", "decide")],
        )


if __name__ == "__main__":
    unittest.main()
