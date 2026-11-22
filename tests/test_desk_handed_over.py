import argparse
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BIN = Path(__file__).resolve().parents[1] / "desk" / "bin"


def load(name: str) -> object:
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(BIN / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class AutoAdoptedThreadTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.backlog = self.home / "desk" / "backlog"
        self.backlog.mkdir(parents=True)
        (self.home / "desk" / "state").mkdir()

    def add_item(self, thread: str, **fields: object) -> None:
        item = {
            "id": thread,
            "title": thread,
            "thread": thread,
            "effort": None,
            "created": "2026-11-01",
            "comments": [],
            **fields,
        }
        (self.backlog / f"{thread}.json").write_text(json.dumps(item))

    def run_script(self, name: str) -> str:
        env = {**os.environ, "HOME": str(self.home)}
        result = subprocess.run([sys.executable, str(BIN / name)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_autostart_resumes_only_threads_handed_over(self) -> None:
        for thread, adopted in (("mine", "auto"), ("handed", None)):
            self.add_item(
                thread, status="open", paused="2026-11-01", unblocked="2026-11-02", **({"adopted": adopted} if adopted else {})
            )
        self.assertEqual(self.run_script("autostart").splitlines()[1:], ["resume handed handed"])

    def test_space_sync_parks_only_threads_handed_over(self) -> None:
        (self.home / "desk" / "state" / "spaces.json").write_text(
            json.dumps({"spaces": ["work"], "off": ["work"], "efforts": {}})
        )
        db = self.home / ".t3" / "userdata" / "statev2.sqlite"
        db.parent.mkdir(parents=True)
        with sqlite3.connect(db) as conn:
            conn.executescript(
                "CREATE TABLE orchestration_v2_projection_threads"
                " (thread_id TEXT, payload_json TEXT, archived_at TEXT, deleted_at TEXT);"
                "CREATE TABLE orchestration_v2_projection_runs (thread_id TEXT, ordinal INTEGER, status TEXT);"
                "CREATE TABLE orchestration_v2_projection_runtime_requests (thread_id TEXT, status TEXT);"
            )
            for thread, adopted in (("mine", "auto"), ("handed", None)):
                conn.execute("INSERT INTO orchestration_v2_projection_threads VALUES (?, '{}', NULL, NULL)", (thread,))
                conn.execute("INSERT INTO orchestration_v2_projection_runs VALUES (?, 1, 'completed')", (thread,))
                self.add_item(thread, status="started", **({"adopted": adopted} if adopted else {}))
        parked = [json.loads(line)["thread"] for line in self.run_script("space-sync").splitlines()]
        self.assertEqual(parked, ["handed"])

    def test_desk_in_an_auto_adopted_thread_keeps_the_hand_over(self) -> None:
        self.add_item("mine", status="started", adopted="auto", title="T3 title", brief="", summary="", kind=None, repo="app")
        brief = self.home / "brief.md"
        brief.write_text("## Goal\nKeep the volume.")
        backlog = load("backlog")
        args = argparse.Namespace(
            thread="mine",
            title="Keep the volume",
            repo="app",
            kind="bugfix",
            summary="Volume jumps.",
            brief_file=str(brief),
            pr=None,
            blocked_by=None,
            status=None,
            note=None,
            effort=None,
        )
        with (
            patch.object(backlog, "BACKLOG", self.backlog),
            patch.object(backlog, "post"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            backlog.adopt(args)  # type: ignore[attr-defined]
        item = json.loads((self.backlog / "mine.json").read_text())
        self.assertEqual((item["title"], item["kind"], item["brief"]), ("Keep the volume", "bugfix", "## Goal\nKeep the volume."))


if __name__ == "__main__":
    unittest.main()
