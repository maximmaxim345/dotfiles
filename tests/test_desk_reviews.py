import importlib
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desk" / "board"))
server = importlib.import_module("server")
reviews = importlib.import_module("reviews")


class RemoteHandler(server.Handler):  # type: ignore[name-defined]
    def remote(self) -> bool:
        return True


class ReviewPageTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.log = self.root / "sent.log"
        stub = self.root / "t3"
        stub.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" >> {self.log}\n")
        stub.chmod(0o755)
        for target, name, value in (
            (reviews, "REVIEWS", self.root / "reviews"),
            (reviews, "T3", stub),
            (server, "STATE", self.root),
            (server, "TOKEN", self.root / "board.token"),
            (server, "LOGIN", self.root / "board.login"),
        ):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.page = self.root / "review-abc1234.html"
        self.page.write_text(self.html("1111"))
        self.review = reviews.register(self.page, "thread-one")

    def html(self, key: str) -> str:
        return f'<!doctype html><script id="kit-data" type="application/json">{{"key": "{key}"}}</script>'

    def comment(self, page: str = "1111", **extra: object) -> dict:
        return {"page": page, "op": "add", "hunk": "h1", "key": "R3", "label": "app.py:3", "text": "why?", **extra}

    def serve(self, handler: type) -> str:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    def request(self, url: str, body: object = None) -> tuple:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as err:
            return err.code, err.read()

    def test_tailnet_review_routes_need_the_login_cookie(self) -> None:
        base = self.serve(RemoteHandler)
        self.assertEqual(self.request(f"{base}/review/{self.review}")[0], 403)
        self.assertEqual(self.request(f"{base}/api/review/{self.review}/state")[0], 403)
        self.assertEqual(self.request(f"{base}/api/review/{self.review}/send", {"text": "go"})[0], 403)
        self.assertFalse(self.log.exists())

    def test_only_registered_pages_are_served(self) -> None:
        base = self.serve(server.Handler)
        secret = self.root / "secret.html"
        secret.write_text("private content")
        self.assertEqual(self.request(f"{base}/review/{self.review}"), (200, self.page.read_bytes()))
        for path in ("/review/secret", "/review/..%2Fsecret.html", f"/review/{self.review}%2F..%2F..%2Fsecret.html"):
            status, body = self.request(base + path)
            self.assertEqual(status, 404, path)
            self.assertNotIn(b"private content", body)

    def test_send_goes_to_the_registered_thread_and_marks_what_went_out(self) -> None:
        base = self.serve(server.Handler)
        self.request(f"{base}/api/review/{self.review}/edit", self.comment())
        body = {"page": "1111", "text": "[1] app.py:3: why?\n", "comments": [1], "picks": {}, "notes": {}, "thread": "t2"}
        status, data = self.request(f"{base}/api/review/{self.review}/send", body)
        self.assertEqual(status, 200)
        self.assertEqual(self.log.read_text().split("\n")[:3], ["thread", "send", "thread-one"])
        self.assertEqual(json.loads(data)["sent"]["comments"], [1])

    def test_edits_from_two_browsers_keep_both_comments_and_the_replies(self) -> None:
        reviews.edit(self.review, self.comment())
        reviews.reply(self.review, 1, "Because.")
        reviews.edit(self.review, self.comment(text="and this?"))
        state = reviews.edit(self.review, {"page": "1111", "op": "resolve", "id": 1, "on": True})
        self.assertEqual([(c["id"], c["text"]) for c in state["state"]["comments"]], [(1, "why?"), (2, "and this?")])
        self.assertEqual([r["text"] for r in state["replies"]["1"]], ["Because."])

    def test_a_rebuilt_page_starts_fresh_and_refuses_edits_from_the_old_one(self) -> None:
        base = self.serve(server.Handler)
        self.request(f"{base}/api/review/{self.review}/edit", self.comment())
        self.page.write_text(self.html("2222"))
        self.assertEqual(self.request(f"{base}/review/{self.review}")[0], 200)
        self.assertEqual(self.request(f"{base}/api/review/{self.review}/edit", self.comment())[0], 409)
        state = reviews.edit(self.review, self.comment(page="2222"))["state"]
        self.assertEqual([c["id"] for c in state["comments"]], [2])


if __name__ == "__main__":
    unittest.main()
