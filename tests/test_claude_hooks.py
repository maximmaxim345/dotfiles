import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "claude" / "hooks"


def run_hook(name: str, event: dict) -> dict:
    output = subprocess.run(
        [sys.executable, str(HOOKS / name)], input=json.dumps(event), capture_output=True, text=True, check=True
    ).stdout
    result: dict = json.loads(output) if output.strip() else {}
    return result


def denied(command: str, cwd: str = "/") -> bool:
    event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
    decision: str | None = run_hook("check-commands.py", event).get("hookSpecificOutput", {}).get("permissionDecision")
    return decision == "deny"


class CheckCommandsTests(unittest.TestCase):
    def test_dash_in_a_body_file_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "body.md").write_text("Fixes the stall \u2014 on reconnect.\n", encoding="utf-8")
            self.assertTrue(denied("gh pr create --title Fix --body-file body.md", folder))
            self.assertFalse(denied("cat body.md", folder))

    def test_drafted_line_passes_while_a_trailer_is_blocked(self) -> None:
        self.assertFalse(denied('gh pr comment 5 --body "Looks good.\n\nDrafted with Claude."'))
        self.assertTrue(denied('git commit -m "fix: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"'))

    def test_caffeinate_is_blocked_only_as_a_command(self) -> None:
        self.assertTrue(denied("make test && caffeinate -i sleep 5"))
        self.assertFalse(denied("grep caffeinate CLAUDE.md"))


class AskLineTests(unittest.TestCase):
    def test_question_above_trailing_links_needs_an_ask_line(self) -> None:
        reply = "Done. Should I open the PR?\n\nhttps://github.com/o/r/compare/main...x?expand=1"
        self.assertEqual(run_hook("ask-line.py", {"last_assistant_message": reply}).get("decision"), "block")
        reply = "Done.\n\nAsk: open the PR as a draft?\n\nhttps://github.com/o/r/pull/5"
        self.assertEqual(run_hook("ask-line.py", {"last_assistant_message": reply}), {})


if __name__ == "__main__":
    unittest.main()
