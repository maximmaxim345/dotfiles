import importlib
import json
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


if __name__ == "__main__":
    unittest.main()
