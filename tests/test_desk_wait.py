import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "desk" / "bin" / "desk-wait"
loader = importlib.machinery.SourceFileLoader("desk_wait", str(SCRIPT))
spec = importlib.util.spec_from_loader("desk_wait", loader)
assert spec
desk_wait = importlib.util.module_from_spec(spec)
loader.exec_module(desk_wait)

MINUTE = 60


class StartPreReadsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.started = Path(folder.name) / "prereads.started"
        self.start_fails = False
        for patcher in (
            patch.object(desk_wait, "PRE_READS_STARTED", self.started),
            patch.object(desk_wait, "WATCH", Path(folder.name) / "watch.json"),
            patch.object(desk_wait.subprocess, "run", self.fake_run),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_run(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if command[1:] == ["due"]:
            lines = "".join(json.dumps({"url": url, "head": head}) + "\n" for url, head in self.due)
            return subprocess.CompletedProcess(command, 0, lines, "")
        self.threads += 1
        return subprocess.CompletedProcess(command, int(self.start_fails), "", "")

    def threads_started(self, due: list[tuple[str, str]], minutes_since_start: dict[str, int]) -> int:
        self.due, self.threads = due, 0
        self.started.write_text(json.dumps({key: time.time() - age * MINUTE for key, age in minutes_since_start.items()}))
        with patch.object(desk_wait, "pre_reads_checked", 0.0):
            desk_wait.start_pre_reads()
        return self.threads

    def test_a_thread_starts_only_for_a_new_head_once_the_last_thread_had_an_hour(self) -> None:
        self.assertEqual(self.threads_started([("pr1", "abc")], {}), 1)
        self.assertEqual(self.threads_started([], {}), 0)
        self.assertEqual(self.threads_started([("pr1", "abc")], {"pr1 abc": 90}), 0)
        self.assertEqual(self.threads_started([("pr1", "abc"), ("pr2", "def")], {"pr1 abc": 90}), 1)
        self.assertEqual(self.threads_started([("pr1", "abc"), ("pr2", "def")], {"pr1 abc": 20}), 0)
        self.assertEqual(self.threads_started([("pr1", "abc")], {"pr1 abc": 130}), 1)

    def test_a_thread_that_failed_to_start_is_tried_again(self) -> None:
        self.start_fails = True
        self.threads_started([("pr1", "abc")], {})
        self.assertEqual(json.loads(self.started.read_text()), {})


if __name__ == "__main__":
    unittest.main()
