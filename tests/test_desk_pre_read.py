import argparse
import importlib
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "desk" / "bin" / "pre-read"
loader = importlib.machinery.SourceFileLoader("pre_read", str(SCRIPT))
spec = importlib.util.spec_from_loader("pre_read", loader)
assert spec
pre_read = importlib.util.module_from_spec(spec)
loader.exec_module(pre_read)
server = importlib.import_module("server")

TODAY = "2026-11-23"
SPACES = {"spaces": ["work"], "off": [], "efforts": {}}


def pr(number: int, sha: str = "abc") -> dict:
    return {
        "html_url": f"https://github.com/acme/widget/pull/{number}",
        "title": f"PR {number}",
        "created_at": f"2026-11-{number:02d}T10:00:00Z",
        "user": {"login": "someone", "type": "User"},
        "draft": False,
        "head": {"sha": sha},
    }


def urls(due: list[dict]) -> list[str]:
    return [p["url"].rsplit("/", 1)[1] for p in due]


def read(number: int, sha: str, at: str) -> dict:
    return {"url": pr(number)["html_url"], "sha": sha, "verdict": "almost", "at": at}


class DuePrsTests(unittest.TestCase):
    def test_a_pre_read_is_redone_only_when_the_head_moved(self) -> None:
        log = [read(1, "abc", "2026-11-20T10:00:00")]
        self.assertEqual(urls(pre_read.due_prs([pr(1)], log, {}, "me", TODAY)), [])
        self.assertEqual(urls(pre_read.due_prs([pr(1, sha="def")], log, {}, "me", TODAY)), ["1"])

    def test_new_heads_get_one_pre_read_a_day_and_every_pre_read_uses_up_the_cap(self) -> None:
        log = [read(1, f"sha{n}", f"{TODAY}T{8 + n:02d}:00:00") for n in range(4)]
        due = pre_read.due_prs([pr(1, sha="sha9"), pr(4), pr(7)], log, {}, "me", TODAY)
        self.assertEqual(urls(due), ["4"])

    def test_an_open_review_item_covers_its_pr(self) -> None:
        brief = "## Goal\n\nReview https://github.com/acme/widget/pull/1\n"
        items = {
            "open": {"kind": "review", "status": "open", "brief": brief},
            "done": {"kind": "review", "status": "done", "brief": brief.replace("/1\n", "/12\n")},
        }
        self.assertEqual(urls(pre_read.due_prs([pr(1), pr(12)], [], items, "me", TODAY)), ["12"])


class SweepTests(unittest.TestCase):
    def test_a_pre_read_pr_that_merged_leaves_now(self) -> None:
        url = pr(5)["html_url"]
        preread = {"sha": "abc", "minutes": 10, "action": "Review now.", "at": f"{TODAY}T09:00:00"}
        entry = {"url": url, "title": "PR 5", "status": "needs-you", "action": "Review now.", "preread": preread, "news": []}
        with tempfile.TemporaryDirectory() as folder:
            incoming = Path(folder) / "incoming.json"
            incoming.write_text(json.dumps({url: entry}))
            with (
                patch.object(pre_read, "INCOMING", incoming),
                patch.object(pre_read, "pull", lambda url: {"state": "closed", "merged_at": "2026-11-23T10:00:00Z"}),
            ):
                pre_read.sweep({})
            entries = list(json.loads(incoming.read_text()).values())
        self.assertEqual(server.now_rows({}, {}, [e for e in entries if server.incoming_shown(e)], None, {}, SPACES), [])


class SaveTests(unittest.TestCase):
    def test_a_saved_pre_read_shows_on_now_with_its_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            incoming = Path(folder) / "incoming.json"
            text = Path(folder) / "pre-read.md"
            text.write_text("Adds a flag.\n")
            url = pr(3)["html_url"]
            args = argparse.Namespace(
                url=url,
                sha="abc",
                title="PR 3",
                verdict="ready",
                minutes=12,
                action="Review now.",
                text_file=str(text),
                draft_file=None,
            )
            with (
                patch.object(pre_read, "INCOMING", incoming),
                patch.object(pre_read, "PREREADS", Path(folder) / "prereads.json"),
                patch.object(pre_read, "pull", lambda url: {"state": "open"}),
            ):
                pre_read.save(args)
            entries = list(json.loads(incoming.read_text()).values())
        rows = server.now_rows({}, {}, entries, None, {}, SPACES)
        self.assertEqual([(r["kind"], r["minutes"], r["url"]) for r in rows], [("review", 12, url)])


if __name__ == "__main__":
    unittest.main()
