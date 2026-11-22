import importlib.machinery
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "desk" / "bin" / "worktree-due"
loader = importlib.machinery.SourceFileLoader("worktree_due", str(SCRIPT))
spec = importlib.util.spec_from_loader("worktree_due", loader)
assert spec
worktree_due = importlib.util.module_from_spec(spec)
loader.exec_module(worktree_due)


class WorktreeDueTests(unittest.TestCase):
    def test_ignored_file_holds_a_pushed_worktree(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        origin, clone = Path(temporary.name) / "origin", Path(temporary.name) / "clone"

        def git(*args: str) -> None:
            subprocess.run(["git", *args], check=True, capture_output=True)

        git("init", "--bare", str(origin))
        git("clone", str(origin), str(clone))
        (clone / ".gitignore").write_text("notes/\nnode_modules/\n")
        git("-C", str(clone), "add", ".gitignore")
        git("-C", str(clone), "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-m", "init")
        git("-C", str(clone), "push", "origin", "HEAD")
        (clone / "node_modules").mkdir()
        (clone / "node_modules" / "x.js").write_text("")
        self.assertIsNone(worktree_due.held_because(str(clone)))
        (clone / "notes").mkdir()
        (clone / "notes" / "contract.md").write_text("only here")
        self.assertIn("notes/", worktree_due.held_because(str(clone)) or "")


if __name__ == "__main__":
    unittest.main()
