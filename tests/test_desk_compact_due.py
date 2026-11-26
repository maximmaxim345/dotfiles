import datetime
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COMPACT_DUE = Path(__file__).resolve().parents[1] / "desk" / "bin" / "compact-due"


class CompactDueTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        (self.home / "desk" / "backlog").mkdir(parents=True)
        (self.home / "desk" / "state").mkdir()
        db = self.home / ".t3" / "userdata" / "statev2.sqlite"
        db.parent.mkdir(parents=True)
        self.conn = sqlite3.connect(db)
        self.addCleanup(self.conn.close)
        self.conn.executescript(
            "CREATE TABLE orchestration_v2_projection_threads"
            " (thread_id TEXT, title TEXT, payload_json TEXT, archived_at TEXT, deleted_at TEXT);"
            "CREATE TABLE orchestration_v2_projection_runs"
            " (run_id TEXT, thread_id TEXT, ordinal INTEGER, status TEXT, completed_at TEXT, provider TEXT);"
            "CREATE TABLE orchestration_v2_projection_turn_items (thread_id TEXT);"
            "CREATE TABLE orchestration_v2_projection_runtime_requests (thread_id TEXT, status TEXT);"
        )

    def add_thread(self, thread: str, idle: datetime.timedelta, asks: bool) -> None:
        ended = datetime.datetime.now(datetime.timezone.utc) - idle
        self.conn.execute(
            "INSERT INTO orchestration_v2_projection_threads VALUES (?, ?, ?, NULL, NULL)",
            (thread, f"app - {thread}", json.dumps({"lineage": {}})),
        )
        self.conn.execute(
            "INSERT INTO orchestration_v2_projection_runs VALUES (?, ?, 1, 'completed', ?, 'claudeAgent')",
            (f"run-{thread}", thread, ended.isoformat()),
        )
        self.conn.executemany("INSERT INTO orchestration_v2_projection_turn_items VALUES (?)", [(thread,)] * 50)
        self.conn.commit()
        item: dict[str, object] = {"id": thread, "thread": thread, "status": "started"}
        if asks:
            item["asks"] = {"text": "Push?", "at": ended.isoformat()}
        (self.home / "desk" / "backlog" / f"{thread}.json").write_text(json.dumps(item))

    def due(self) -> dict[str, list[dict[str, str]]]:
        result = subprocess.run(
            [sys.executable, str(COMPACT_DUE)], env={**os.environ, "HOME": str(self.home)}, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        due: dict[str, list[dict[str, str]]] = json.loads(result.stdout) if result.stdout else {"compact": [], "settle": []}
        return due

    def listed(self, due: dict[str, list[dict[str, str]]]) -> set[str]:
        return {entry["thread"] for key in ("compact", "settle") for entry in due[key]}

    def test_thread_that_waits_on_me_is_held_while_others_are_listed(self) -> None:
        self.add_thread("asking", datetime.timedelta(minutes=55), asks=True)
        self.add_thread("quiet", datetime.timedelta(minutes=55), asks=False)
        self.assertEqual(self.listed(self.due()), {"quiet"})

    def test_thread_that_waits_on_me_is_compacted_after_a_day(self) -> None:
        self.add_thread("asking", datetime.timedelta(hours=25), asks=True)
        due = self.due()
        self.assertEqual([entry["thread"] for entry in due["compact"]], ["asking"])
        self.assertEqual(due["settle"], [])

    def test_settled_routine_thread_is_archived_after_a_week(self) -> None:
        settled = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)).isoformat()
        payload = {"lineage": {}, "settledOverride": "settled", "settledAt": settled}
        self.conn.execute(
            "INSERT INTO orchestration_v2_projection_threads VALUES ('old', 'routine - pre-reads', ?, NULL, NULL)",
            (json.dumps(payload),),
        )
        self.conn.commit()
        self.assertEqual([entry["thread"] for entry in self.due()["archive"]], ["old"])


if __name__ == "__main__":
    unittest.main()
