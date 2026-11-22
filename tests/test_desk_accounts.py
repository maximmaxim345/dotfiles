import importlib.machinery
import importlib.util
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "desk" / "bin" / "accounts"
loader = importlib.machinery.SourceFileLoader("accounts", str(SCRIPT))
spec = importlib.util.spec_from_loader("accounts", loader)
assert spec
accounts = importlib.util.module_from_spec(spec)
loader.exec_module(accounts)

CONFIG = {
    "repos": {
        "~/code/home/*": {"claude": ["home"], "reviewer": "other"},
        "me/*": {"claude": ["home"], "reviewer": "other"},
        "acme/*": {"claude": ["acme", "work"], "reviewer": "copilot"},
    },
}


def checkout(folder: str, **remotes: str) -> Path:
    subprocess.run(["git", "init", "-q", folder], check=True)
    for remote, url in remotes.items():
        subprocess.run(["git", "-C", folder, "remote", "add", remote, url], check=True)
    return Path(folder)


class AccountsTests(unittest.TestCase):
    def test_a_fork_of_a_work_repo_uses_the_work_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            name = accounts.github_name(
                checkout(folder, origin="git@github.com:me/widget.git", upstream="https://github.com/acme/widget")
            )
        self.assertEqual(accounts.pick(CONFIG, name, None), {"claude": ["acme", "work"], "reviewer": "copilot"})

    def test_a_fork_without_upstream_maps_by_its_parent_or_not_at_all(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            fork = checkout(folder, origin="git@github.com:me/widget.git")
            with patch.object(accounts, "parent_of", lambda name: "acme/widget"):
                self.assertEqual(accounts.pick(CONFIG, accounts.github_name(fork), None)["claude"], ["acme", "work"])
            with patch.object(accounts, "parent_of", lambda name: None):
                self.assertEqual(accounts.pick(CONFIG, accounts.github_name(fork), None)["claude"], [])

    def test_a_project_title_resolves_to_the_project_whose_folder_exists(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "state.sqlite"
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE projection_projects (title TEXT, workspace_root TEXT, deleted_at TEXT)")
            for root in (Path(folder) / "gone", Path(folder)):
                conn.execute("INSERT INTO projection_projects VALUES ('widget', ?, NULL)", (str(root),))
            conn.commit()
            conn.close()
            with patch.object(accounts, "T3_DB", db):
                self.assertEqual(accounts.checkout_of("widget"), Path(folder))

    def test_a_checkout_path_pattern_covers_repos_without_a_github_remote(self) -> None:
        checkout = Path("~/code/home/notes").expanduser()
        self.assertEqual(accounts.pick(CONFIG, None, checkout)["claude"], ["home"])
        self.assertEqual(accounts.pick(CONFIG, None, Path("/elsewhere/notes")), {"claude": [], "reviewer": None})


if __name__ == "__main__":
    unittest.main()
