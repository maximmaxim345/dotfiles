import importlib.machinery
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

BOARD_THREADS = Path(__file__).resolve().parents[1] / "desk" / "bin" / "board-threads"
loader = importlib.machinery.SourceFileLoader("board_threads", str(BOARD_THREADS))
spec = importlib.util.spec_from_loader("board_threads", loader)
assert spec is not None
board_threads = importlib.util.module_from_spec(spec)
loader.exec_module(board_threads)


class CommittedOnBranchTests(unittest.TestCase):
    def git(self, *args: str, committer: str = "me@example.com") -> None:
        env = {**os.environ, "GIT_COMMITTER_NAME": "c", "GIT_COMMITTER_EMAIL": committer, "GIT_CONFIG_GLOBAL": os.devnull}
        subprocess.run(["git", "-C", str(self.clone), *args], check=True, capture_output=True, env=env)

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        origin, self.clone = Path(temporary.name) / "origin", Path(temporary.name) / "clone"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(origin), str(self.clone)], check=True, capture_output=True)
        self.git("config", "user.email", "me@example.com")
        self.git("config", "user.name", "me")
        self.git("commit", "-q", "--allow-empty", "-m", "base")
        self.git("push", "-q", "origin", "main")
        self.git("remote", "set-head", "origin", "main")

    def test_only_my_commits_on_a_branch_count(self) -> None:
        self.git("switch", "-q", "-c", "their-pr")
        self.git("commit", "-q", "--allow-empty", "-m", "theirs", committer="them@example.com")
        self.assertFalse(board_threads.committed_on_branch(str(self.clone), "their-pr"))
        self.git("commit", "-q", "--allow-empty", "-m", "mine")
        self.assertTrue(board_threads.committed_on_branch(str(self.clone), "their-pr"))


if __name__ == "__main__":
    unittest.main()
