import contextlib
import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "desk" / "bin" / "corrections"
loader = importlib.machinery.SourceFileLoader("corrections", str(SCRIPT))
spec = importlib.util.spec_from_loader("corrections", loader)
assert spec
corrections = importlib.util.module_from_spec(spec)
loader.exec_module(corrections)


class CorrectionsTests(unittest.TestCase):
    def run_script(self, *argv: str) -> str:
        out = io.StringIO()
        with (
            patch.object(sys, "argv", ["corrections", *argv]),
            patch.object(corrections, "require_desk_home", lambda: None),
            contextlib.redirect_stdout(out),
        ):
            corrections.main()
        return out.getvalue()

    def test_a_proposed_correction_leaves_the_list_and_the_others_stay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            with patch.object(corrections, "STATE", state), patch.object(corrections, "CORRECTIONS", state / "c.json"):
                self.run_script("add", "--did", "pushed a fix unasked", "--wanted", "ask first")
                self.run_script("add", "--did", "wrote a long brief", "--wanted", "a short one", "--rule", "review-brief")
                self.run_script("proposed", "1", "--item", "push-rule")
                listed = [json.loads(line) for line in self.run_script("list").splitlines()]
        self.assertEqual([(e["id"], e["did"], e.get("rule")) for e in listed], [(2, "wrote a long brief", "review-brief")])


if __name__ == "__main__":
    unittest.main()
