import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desk" / "board"))
server = importlib.import_module("server")


class StartOnAnotherMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "backlog").mkdir()
        (self.root / "machines.json").write_text(json.dumps([{"name": "Laptop", "environmentId": "env-1"}]))
        for name, value in (
            ("BACKLOG", self.root / "backlog"),
            ("STATE", self.root),
            ("EVENTS", self.root / "events.jsonl"),
            ("MACHINES", self.root / "machines.json"),
        ):
            patcher = patch.object(server, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, **fields: object) -> None:
        item = {"id": "a", "title": "A", "status": "open", "comments": [], **fields}
        (self.root / "backlog" / "a.json").write_text(json.dumps(item))

    def started_on(self) -> tuple:
        item = json.loads((self.root / "backlog" / "a.json").read_text())
        return item.get("machine"), bool((item.get("start_note") or {}).get("draft_pr"))

    def test_a_start_on_a_listed_machine_grants_the_draft_pr_until_i_start_it_here(self) -> None:
        self.write()
        server.set_status(["a"], "requested", {"text": "", "machine": "Laptop"})
        self.assertEqual(self.started_on(), ("Laptop", True))
        item = json.loads((self.root / "backlog" / "a.json").read_text())
        self.write(**{**item, "needs": "Laptop is offline"})
        server.set_status(["a"], "requested", here=True)
        self.assertEqual(self.started_on(), (None, False))

    def test_an_item_with_a_thread_stays_on_its_machine(self) -> None:
        self.write(thread="t-1", machine="Laptop")
        server.set_status(["a"], "requested", {"text": "", "machine": ""})
        self.assertEqual(self.started_on(), ("Laptop", True))
        self.write(thread="t-2")
        server.set_status(["a"], "requested", {"text": "", "machine": "Laptop"})
        self.assertEqual(self.started_on(), (None, False))


class AnotherMachineTests(unittest.TestCase):
    def test_another_machine_reads_the_backlog_but_registers_no_review_page(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            (Path(home) / "desk" / "backlog").mkdir(parents=True)
            page = Path(home) / "review.html"
            page.write_text("<html></html>")
            env = {**os.environ, "HOME": home}
            bin_dir = Path(__file__).resolve().parents[1] / "desk" / "bin"
            listed = subprocess.run([sys.executable, str(bin_dir / "backlog"), "list"], env=env, capture_output=True)
            register = [sys.executable, str(bin_dir / "review-page"), "register", "--page", str(page), "--thread", "t-1"]
            registered = subprocess.run(register, env=env, capture_output=True, text=True)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("not the desk's machine", registered.stderr)
            self.assertFalse((Path(home) / "desk" / "state").exists())


if __name__ == "__main__":
    unittest.main()
