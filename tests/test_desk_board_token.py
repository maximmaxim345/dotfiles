import importlib
import stat
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


class RemoteHandler(server.Handler):  # type: ignore[name-defined]
    def remote(self) -> bool:
        return True


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object) -> None:
        return None


class BoardTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        state = Path(temporary.name)
        for name, value in (("STATE", state), ("TOKEN", state / "board.token"), ("LOGIN", state / "board.login")):
            patcher = patch.object(server, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), RemoteHandler)
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def status(self, path: str, cookie: str = "") -> int:
        request = urllib.request.Request(self.base + path, headers={"Cookie": cookie} if cookie else {})
        try:
            with urllib.request.build_opener(NoRedirect).open(request) as response:
                return int(response.status)
        except urllib.error.HTTPError as err:
            return err.code

    def test_tailnet_request_without_the_token_cookie_is_refused(self) -> None:
        self.assertEqual(self.status("/"), 403)
        self.assertEqual(self.status("/", cookie="desk_token=guess"), 403)

    def test_login_link_sets_a_working_cookie_once(self) -> None:
        url = server.login_url("127.0.0.1", self.httpd.server_address[1])
        path = url.split(str(self.httpd.server_address[1]), 1)[1]
        with self.assertRaises(urllib.error.HTTPError) as redirect:
            urllib.request.build_opener(NoRedirect).open(self.base + path)
        self.assertEqual(redirect.exception.code, 303)
        cookie = redirect.exception.headers["Set-Cookie"].split(";", 1)[0]
        self.assertEqual(self.status("/", cookie=cookie), 200)
        self.assertEqual(self.status(path), 403)
        self.assertEqual(stat.S_IMODE(server.TOKEN.stat().st_mode), 0o600)

    def test_empty_token_and_login_files_let_nobody_in(self) -> None:
        server.TOKEN.write_text("")
        server.LOGIN.write_text("")
        self.assertEqual(self.status("/", cookie="desk_token="), 403)
        self.assertEqual(self.status("/login?code="), 403)


if __name__ == "__main__":
    unittest.main()
