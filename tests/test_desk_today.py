import datetime
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desk" / "board"))
server = importlib.import_module("server")


def item(item_id: str, minutes: int = 20, **fields: object) -> dict:
    return {
        "id": item_id,
        "title": item_id,
        "status": "open",
        "created": "2026-11-01",
        "minutes": minutes,
        "comments": [],
        **fields,
    }


class TodayRowsTests(unittest.TestCase):
    def rows(self, items: list[dict], moves: dict[str, str], budget: int, waiting: int = 0) -> dict[str, bool]:
        by_id = {i["id"]: i for i in items}
        plan = {"order": [i["id"] for i in items], "moves": moves}
        return {row["id"]: row["today"] for row in server.today_rows(by_id, plan, budget, waiting)}

    def test_the_line_falls_where_the_minutes_run_out_and_stays_there(self) -> None:
        items = [item("a", 30), item("b", 30), item("c", 5)]
        self.assertEqual(self.rows(items, {}, 60, waiting=10), {"a": True, "b": False, "c": False})

    def test_urgent_items_and_my_moves_ignore_the_line(self) -> None:
        items = [item("a", 30), item("b", 30), item("c", 30, urgent=True), item("d", 30)]
        self.assertEqual(self.rows(items, {"a": "later", "d": "today"}, 30), {"a": False, "b": True, "c": True, "d": True})


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


class FillTodayTests(unittest.TestCase):
    def test_my_next_column_moves_onto_today_in_its_order(self) -> None:
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "BACKLOG", Path(folder)):
            items = {"b": item("b", status="next", rank=2), "a": item("a", status="next", rank=1), "c": item("c")}
            for entry in items.values():
                (Path(folder) / f"{entry['id']}.json").write_text(json.dumps(entry))
            plan = server.fill_today(items, {}, "2026-11-23")
            saved = json.loads((Path(folder) / "b.json").read_text())
        self.assertEqual(plan["order"][:2], ["a", "b"])
        self.assertEqual(plan["moves"], {"a": "today", "b": "today"})
        self.assertEqual((saved["status"], "rank" in saved, saved["comments"][0]["by"]), ("open", False, "desk"))


class NowRowsTests(unittest.TestCase):
    def test_someone_waiting_comes_first_then_quick_questions(self) -> None:
        asks = {"kind": "review", "text": "Review?", "at": "2026-11-20T10:00:00+00:00"}
        items = {
            "review": item("review", status="started", thread="t1", asks=asks),
            "push": item("push", status="started", thread="t2", asks={**asks, "kind": "push", "text": "Push?"}),
        }
        incoming = [{"url": "u", "title": "issue", "status": "needs-you", "updated": "2026-11-21T10:00:00Z"}]
        rows = server.now_rows(items, {}, incoming, None, {})
        self.assertEqual([row["kind"] for row in rows], ["reply", "push", "review"])


if __name__ == "__main__":
    unittest.main()
