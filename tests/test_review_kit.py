import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[1] / "claude" / "review-kit" / "build_review.py"
spec = importlib.util.spec_from_file_location("build_review", KIT)
assert spec and spec.loader
build_review = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_review
spec.loader.exec_module(build_review)

FUNCTIONS = "".join(f"def helper_{i}(value):\n    return value + {i}\n\n\n" for i in range(40))


class ReviewKitTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        environment = patch.dict(
            os.environ,
            {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@example.com",
            },
        )
        environment.start()
        self.addCleanup(environment.stop)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def write(self, name: str, text: str) -> None:
        (self.repo / name).write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def build_page(self, narrative: dict) -> str:
        self.write("app.py", FUNCTIONS)
        self.write("old.txt", "remove me\n")
        self.write("moved.txt", "same content\n" * 5)
        self.commit("initial")
        self.git("checkout", "-q", "-b", "feat/demo")
        self.write("app.py", FUNCTIONS.replace("value + 2\n", "value * 2\n").replace("value + 35\n", "value * 35\n"))
        (self.repo / "old.txt").unlink()
        self.git("mv", "moved.txt", "renamed.txt")
        self.write("README.md", "A new paragraph of prose.\n")
        (self.repo / "logo.bin").write_bytes(b"\x00\x01\x02")
        self.commit("change")
        narrative_path = self.root / "narrative.json"
        narrative_path.write_text(json.dumps(narrative), encoding="utf-8")
        output = self.root / "page.html"
        argv = ["review", "--repo", str(self.repo), "--base", "main", "--narrative", str(narrative_path), "-o", str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_review.main(argv), 0)
        return output.read_text(encoding="utf-8")

    def hunk_ids(self) -> list:
        change = build_review.collect(self.repo, "main", None, None, False, None)
        return [h.id for h in change.hunks]

    def test_every_hunk_appears_exactly_once(self) -> None:
        narrative = {
            "groups": [
                {"title": "Core", "hunks": [{"file": "app.py", "lines": "8", "note": "First."}]},
                {"title": "Again", "hunks": [{"file": "app.py", "lines": "8", "note": "Repeated."}]},
                {"unimportant": True, "reason": "Docs only", "hunks": [{"file": "README.md"}]},
            ]
        }
        page = self.build_page(narrative)
        ids = self.hunk_ids()
        self.assertEqual(len(ids), 6)
        for hunk_id in ids:
            self.assertEqual(page.count(f'data-hunk="{hunk_id}"'), 1, hunk_id)

    def test_unmentioned_hunks_are_kept_in_the_last_group(self) -> None:
        page = self.build_page({"groups": [{"title": "Core", "hunks": [{"file": "app.py"}]}]})
        mentioned, unmentioned = page.split('<section class="group unmentioned">')
        change = build_review.collect(self.repo, "main", None, None, False, None)
        for hunk in change.hunks:
            self.assertIn(f'data-hunk="{hunk.id}"', mentioned if hunk.path == "app.py" else unmentioned, hunk.path)

    def two_commit_branch(self) -> None:
        self.write("app.py", FUNCTIONS)
        self.commit("initial")
        self.git("checkout", "-q", "-b", "feat/demo")
        self.write("app.py", FUNCTIONS.replace("value + 2\n", "value * 2\n"))
        self.commit("first")
        self.write("app.py", FUNCTIONS.replace("value + 2\n", "value * 2\n").replace("value + 35\n", "value - 35\n"))
        self.commit("second")
        self.git("checkout", "-q", "main")

    def test_page_names_come_from_the_range_and_remote_not_the_checkout(self) -> None:
        self.two_commit_branch()
        self.git("remote", "add", "origin", "https://example.com/acme/widget.git")
        output = self.root / "page.html"
        argv = ["review", "--repo", str(self.repo), "--range", "main..feat/demo", "-o", str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_review.main(argv), 0)
        page = output.read_text(encoding="utf-8")
        self.assertIn("<title>Review: widget feat/demo</title>", page)
        self.assertIn("branch <code>feat/demo</code>", page)
        self.assertNotIn("<code>main</code>", page)

    def test_list_hunks_json_names_ranges_and_commits(self) -> None:
        self.two_commit_branch()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            build_review.main(["review", "--repo", str(self.repo), "--range", "main..feat/demo", "--list-hunks", "--json"])
        data = json.loads(out.getvalue())
        subjects = {c["sha"]: c["subject"] for c in data["commits"]}
        self.assertEqual(list(subjects.values()), ["first", "second"])
        rows = [(h["changed"], h["hunk"], [subjects[c] for c in h["commits"]]) for h in data["hunks"]]
        self.assertEqual(rows, [("10", "7-13", ["first"]), ("142", "139-145", ["second"])])
        self.assertEqual(data["tier"], "small")

    def test_path_line_in_text_links_only_lines_the_page_shows(self) -> None:
        narrative = {"decide": [{"title": "Q", "evidence": "See `app.py:10` and app.py:155, not app.py:900 or lib.py:3."}]}
        page = self.build_page(narrative)
        self.assertEqual(re.findall(r'data-lines="([\d-]+)"', page), ["10-10", "155-155"])

    def test_look_closely_paths_raise_the_tier_and_mark_the_hunk(self) -> None:
        paths = self.root / "review-paths.json"
        paths.write_text(json.dumps({"Acme/Widget": {"api/**": "the public API"}}), encoding="utf-8")
        self.write("app.py", FUNCTIONS)
        (self.repo / "api").mkdir()
        self.write("api/client.py", "TIMEOUT = 5\n")
        self.commit("initial")
        self.git("remote", "add", "origin", "git@example.com:acme/widget.git")
        self.write("api/client.py", "TIMEOUT = 10\n")
        self.write("app.py", FUNCTIONS.replace("value + 2\n", "value * 2\n"))
        with patch.object(build_review, "REVIEW_PATHS", paths):
            change = build_review.collect(self.repo, "main", None, None, True, None)
        self.assertEqual({h.path: h.look for h in change.hunks}, {"api/client.py": "the public API", "app.py": ""})
        self.assertEqual(build_review.pick_tier({"tier": "small"}, change.hunks, False)[0], "normal")

    def test_round_two_after_rebase_and_amend_shows_only_the_fix(self) -> None:
        self.write("app.py", FUNCTIONS)
        self.commit("initial")
        self.git("checkout", "-q", "-b", "feat/demo")
        self.write("app.py", FUNCTIONS.replace("value + 2\n", "value * 2\n"))
        reviewed = self.commit("first round")
        self.git("checkout", "-q", "main")
        self.write("version.py", "VERSION = 2\n")
        self.commit("unrelated change on main")
        self.git("checkout", "-q", "feat/demo")
        self.write("app.py", FUNCTIONS.replace("value + 2\n", "value * 2\n").replace("value + 30\n", "value - 30\n"))
        self.git("commit", "-q", "-a", "--amend", "--no-edit")
        self.git("rebase", "-q", "main")

        change = build_review.collect(self.repo, "main", None, None, False, reviewed)

        changed = [(h.path, kind + text) for h in change.hunks for kind, text in h.lines if kind != " "]
        self.assertEqual(changed, [("app.py", "-    return value + 30"), ("app.py", "+    return value - 30")])

    def test_page_lines_match_git_diff_with_carriage_returns_and_no_final_newline(self) -> None:
        files = {
            "crlf.txt": (b"one\r\ntwo\r\n", b"one\ntwo\r\n"),
            "cr.txt": (b"alpha\n", b"be\rta\n"),
            "eol.txt": (b"last", b"last\n"),
        }
        for name, (old, _) in files.items():
            (self.repo / name).write_bytes(old)
        self.commit("initial")
        for name, (_, new) in files.items():
            (self.repo / name).write_bytes(new)
        self.commit("change")
        output = self.root / "page.html"
        with contextlib.redirect_stdout(io.StringIO()):
            build_review.main(["review", "--repo", str(self.repo), "--range", "HEAD~1..HEAD", "-o", str(output)])
        data = json.loads(re.findall(r'<script id="kit-data" type="application/json">(.*?)</script>', output.read_text())[0])
        shown = []
        for hunk in data["hunks"].values():
            for index, (kind, text) in enumerate(hunk["lines"]):
                shown += [kind + text] + (["\\ No newline at end of file"] if index in hunk["noNewline"] else [])
        diff = subprocess.run(["git", "diff", *build_review.DIFF_ARGS, "HEAD~1", "HEAD"], cwd=self.repo, capture_output=True)
        lines = diff.stdout.decode().split("\n")
        self.assertEqual(shown, [line for line in lines if line and line[0] in " +-\\" and not line.startswith(("--- ", "+++ "))])

    def test_narrative_text_never_reaches_the_page_as_markup(self) -> None:
        ref = {
            "file": "app.py",
            "lines": "10-12",
            "note": "x",
            "look": "x",
            "context": [{"file": "app.py", "lines": "1-2", "note": "x"}],
        }
        narrative = {
            **dict.fromkeys(("title", "repo", "branch", "summary", "worst_case", "tested", "tier_reason", "decide_order"), "x"),
            **dict.fromkeys(("claims_note", "reviewers_note"), "x"),
            "meta": ["x"],
            "facts": [{"label": "x", "text": "x"}],
            "decide": [
                {
                    **dict.fromkeys(("title", "risk_level", "undo", "risk", "evidence", "pick", "why"), "x"),
                    "refs": [ref],
                    "context": [{"file": "app.py", "lines": "1-2", "note": "x"}],
                    "options": [{"id": "x", "text": "x"}],
                }
            ],
            "behavior": {"rows": [{"case": "x", "before": "x", "after": "x"}], "unchanged": "x"},
            "claims": [{"claim": "x", "proof": "test", "name": "x", "fails_without": "x", "detail": "x", "refs": [ref]}],
            "reviewers": [{"name": "x", "fixed": ["x"], "kept": [{"finding": "x", "why": "x"}], "skipped": "x", "note": "x"}],
            "groups": [
                {"title": "x", "note": "x", "hunks": [ref]},
                {"unimportant": "x", "reason": "x", "hunks": [{"file": "README.md"}]},
            ],
        }
        markup = '"><i data-x>'
        page = self.build_page(json.loads(json.dumps(narrative).replace('"x"', json.dumps(markup))))
        self.assertNotIn("<i data-x", page)

    def test_only_web_addresses_in_text_become_links(self) -> None:
        text = build_review.inline('See https://example.com/a?b=1&c="2". Not javascript:alert(1) or `https://example.com/x`.')
        self.assertIn('<a href="https://example.com/a?b=1&amp;c=" target="_blank"', text)
        self.assertNotIn("javascript:alert(1)</a>", text)
        self.assertIn("<code>https://example.com/x</code>", text)
        self.assertNotIn("<a ", build_review.choices([{"text": "See https://example.com/a"}], "A", "x")[1])

    def test_svg_keeps_only_listed_elements_and_local_references(self) -> None:
        drawing = (
            '<svg viewBox="0 0 9 9"><defs><marker id="a"><path d="M0 0L1 1"/></marker></defs><line marker-end="url(#a)"/></svg>'
        )
        self.assertIn('marker-end="url(#a)"', build_review.svg_block(drawing))
        for unsafe in (
            '<svg onload="alert(1)"></svg>',
            "<svg></svg><img src=x onerror=alert(1)>",
            '<svg><image href="https://example.com/x.png"/></svg>',
            '<svg><rect fill="url(https://example.com/x)"/></svg>',
            '<svg><rect fill="\\75 rl(//example.com/x#a)"/></svg>',
            "<svg><style>@import url(https://example.com/x.css);</style></svg>",
        ):
            with self.subTest(unsafe=unsafe), self.assertRaises(build_review.KitError):
                build_review.svg_block(unsafe)


if __name__ == "__main__":
    unittest.main()
