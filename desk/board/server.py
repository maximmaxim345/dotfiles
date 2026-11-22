#!/usr/bin/env python3
"""Serve the desk board on localhost, and with a token on the tailnet address in ~/desk/board.json when one is set."""

from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hmac
import ipaddress
import json
import os
import re
import secrets
import sqlite3
import sys
import tempfile
import threading
import time
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qs, urlsplit

DESK = Path.home() / "desk"
BACKLOG = DESK / "backlog"
EFFORTS = DESK / "efforts"
PAGE = Path(__file__).resolve().parent / "index.html"
STATE = DESK / "state"
T3_DB = Path.home() / ".t3" / "userdata" / "statev2.sqlite"
EXTRA_REPOS = DESK / "repos.json"
THREADS = STATE / "threads.json"
EVENTS = STATE / "events.jsonl"
LISTENER = STATE / "listener.pid"
INCOMING = STATE / "incoming.json"
PROPOSALS = STATE / "proposals.json"
AUTOSTART = STATE / "autostart.json"
AUTOSTART_MODES = {"off", "focus", "all"}
SPACES = STATE / "spaces.json"
DEFAULT_SPACE = "work"
SPACE_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,30}")
SHOWN_INCOMING = {"new", "needs-you", "waiting"}
CHAT_SHOWN_FOR = datetime.timedelta(days=1)
SHOWN_PROPOSALS = {"open", "approved", "failed"}
SETTABLE_STATUSES = {"open", "next", "requested", "done", "dropped"}
CLOSED_STATUSES = {"done", "dropped"}
START_GRANTS = ("draft_pr", "babysit", "second_opinion")
BOARD_CONFIG = DESK / "board.json"
TOKEN = STATE / "board.token"
LOGIN = STATE / "board.login"
LOGIN_FOR = 10 * 60
COOKIE = "desk_token"
FAILED_IN_A_ROW = 3
SWEEP_HOUR = 9
SWEEP_GRACE = datetime.timedelta(hours=2)
SWEEP_EARLY = datetime.timedelta(hours=12)


def tailnet_address() -> str | None:
    address = json.loads(BOARD_CONFIG.read_text()).get("tailnet") if BOARD_CONFIG.exists() else None
    if address:
        try:
            valid = not ipaddress.IPv4Address(address).is_unspecified
        except ValueError:
            valid = False
        if not valid:
            sys.exit(f"{BOARD_CONFIG}: tailnet must be the Mac's Tailscale IPv4 address, not {address}")
    return address


def new_secret(path: Path, nbytes: int) -> str:
    """Write a random secret readable only by me and return it."""
    STATE.mkdir(exist_ok=True)
    secret = secrets.token_urlsafe(nbytes)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
        f.write(secret)
    return secret


def board_token() -> str:
    return TOKEN.read_text().strip() if TOKEN.exists() else new_secret(TOKEN, 32)


def login_url(address: str, port: int) -> str:
    LOGIN.unlink(missing_ok=True)
    return f"http://{address}:{port}/login?code={new_secret(LOGIN, 16)}"


def write_json(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    """Hold an exclusive lock for a read-modify-write of path."""
    with open(path.with_name(path.name + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def item_path(item_id: str) -> Path:
    path = BACKLOG / f"{item_id}.json"
    if path.parent != BACKLOG or not path.exists():
        raise FileNotFoundError(item_id)
    return path


def efforts() -> list[dict]:
    result = []
    for status in sorted(EFFORTS.glob("*/status.md")):
        heading = next((line[2:].strip() for line in status.read_text().splitlines() if line.startswith("# ")), None)
        result.append({"slug": status.parent.name, "title": heading or status.parent.name})
    return result


def repos() -> list[str]:
    """Names of T3 projects that are git repos, plus the names listed in repos.json."""
    rows = []
    if T3_DB.exists():
        conn = sqlite3.connect(f"file:{T3_DB}?mode=ro", uri=True)
        try:
            rows = conn.execute("SELECT title, workspace_root FROM projection_projects WHERE deleted_at IS NULL").fetchall()
        finally:
            conn.close()
    names = {title for title, root in rows if (Path(root) / ".git").exists()}
    if EXTRA_REPOS.exists():
        names.update(json.loads(EXTRA_REPOS.read_text()))
    return sorted(names)


def check_repo(repo: str | None) -> None:
    known = repos()
    if repo and repo not in known:
        raise ValueError(f"unknown repo {repo}, use one of: {', '.join(known)}")


def listening() -> bool:
    try:
        os.kill(int(LISTENER.read_text()), 0)
    except (OSError, ValueError):
        return False
    return True


def last_sweep_due(now: datetime.datetime) -> datetime.datetime:
    """The latest weekday morning sweep time that lies at least SWEEP_GRACE in the past."""
    due = (now - SWEEP_GRACE).replace(hour=SWEEP_HOUR, minute=0, second=0, microsecond=0)
    if due > now - SWEEP_GRACE:
        due -= datetime.timedelta(days=1)
    while due.weekday() >= 5:
        due -= datetime.timedelta(days=1)
    return due


def desk_health() -> dict | None:
    """How many of the desk thread's latest runs failed in a row, and whether its morning sweep is overdue."""
    if not T3_DB.exists():
        return None
    conn = sqlite3.connect(f"file:{T3_DB}?mode=ro", uri=True)
    try:
        roots = conn.execute("SELECT project_id, workspace_root FROM projection_projects WHERE deleted_at IS NULL").fetchall()
        project = next((pid for pid, root in roots if Path(root).resolve() == DESK.resolve()), None)
        row = conn.execute(
            "SELECT thread_id FROM orchestration_v2_projection_threads"
            " WHERE project_id = ? AND title = 'desk' AND archived_at IS NULL AND deleted_at IS NULL",
            (project,),
        ).fetchone()
        if row is None:
            return None
        statuses = conn.execute(
            "SELECT status FROM orchestration_v2_projection_runs WHERE thread_id = ?"
            " AND status IN ('completed', 'failed', 'cancelled', 'interrupted') ORDER BY ordinal DESC LIMIT 50",
            (row[0],),
        ).fetchall()
        (last_sweep,) = conn.execute(
            "SELECT MAX(r.completed_at) FROM orchestration_v2_projection_runs r"
            " JOIN orchestration_v2_projection_messages m ON m.run_id = r.run_id"
            " WHERE r.thread_id = ? AND r.status = 'completed' AND m.thread_id = r.thread_id AND m.role = 'user'"
            " AND json_extract(m.payload_json, '$.text') LIKE 'Morning sweep%'",
            (row[0],),
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    failed = next((n for n, (status,) in enumerate(statuses) if status != "failed"), len(statuses))
    swept = datetime.datetime.fromisoformat(last_sweep.replace("Z", "+00:00")) if last_sweep else None
    due = last_sweep_due(datetime.datetime.now().astimezone())
    return {
        "failed": failed if failed >= FAILED_IN_A_ROW else 0,
        "lastSweep": swept.astimezone().isoformat(timespec="minutes") if swept else None,
        "sweepStale": swept is None or swept < due - SWEEP_EARLY,
    }


def log_event(event: dict) -> None:
    STATE.mkdir(exist_ok=True)
    event["at"] = datetime.datetime.now().isoformat(timespec="seconds")
    with EVENTS.open("a") as f:
        f.write(json.dumps(event) + "\n")


def handed_over(item: dict) -> bool:
    """Whether the desk may act on the item's thread, which it may not for a thread I started that it adopted on its own."""
    return item.get("adopted") != "auto"


def open_blockers(item: dict, items: dict[str, dict]) -> list[str]:
    return [b for b in item.get("blockedBy") or [] if b not in items or items[b]["status"] not in CLOSED_STATUSES]


def autostart_setting() -> dict:
    return json.loads(AUTOSTART.read_text()) if AUTOSTART.exists() else {"mode": "off", "efforts": [], "reviews": False}


def spaces_setting() -> dict:
    return json.loads(SPACES.read_text()) if SPACES.exists() else {"spaces": [DEFAULT_SPACE], "off": [], "efforts": {}}


def space_of(effort: str | None, setting: dict) -> str:
    return setting["efforts"].get(effort or "", DEFAULT_SPACE)


def change_spaces(body: dict) -> None:
    with locked(SPACES):
        setting = spaces_setting()
        if "create" in body:
            name = body["create"].strip().lower()
            if not SPACE_NAME.fullmatch(name):
                raise ValueError("use letters, digits and dashes for a space name")
            if name not in setting["spaces"]:
                setting["spaces"].append(name)
        elif body["space"] not in setting["spaces"]:
            raise ValueError(f"unknown space {body['space']}")
        elif "effort" in body:
            if body["effort"] not in {e["slug"] for e in efforts()}:
                raise ValueError(f"unknown effort {body['effort']}")
            setting["efforts"][body["effort"]] = body["space"]
        elif body["on"]:
            setting["off"] = [s for s in setting["off"] if s != body["space"]]
        elif body["space"] not in setting["off"]:
            setting["off"].append(body["space"])
        write_json(SPACES, setting)
    if "create" not in body:
        log_event({"type": "space"})


def all_items() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(BACKLOG.glob("*.json"))}


def incoming_shown(entry: dict) -> bool:
    """Show open entries unless snoozed, and others except dismissed while my chat waits or a day after its answer."""
    now = datetime.datetime.now()
    if entry.get("snoozed", "") > now.date().isoformat():
        return False
    if entry["status"] in SHOWN_INCOMING:
        return True
    chat = entry.get("chat")
    if entry["status"] == "dismissed" or not chat:
        return False
    return chat[-1]["by"] == "me" or datetime.datetime.fromisoformat(chat[-1]["at"]) > now - CHAT_SHOWN_FOR


def load_state() -> dict:
    items = list(all_items().values())
    threads = json.loads(THREADS.read_text()) if THREADS.exists() else None
    incoming = json.loads(INCOMING.read_text()) if INCOMING.exists() else {}
    proposals = json.loads(PROPOSALS.read_text()) if PROPOSALS.exists() else []
    return {
        "items": items,
        "threads": threads,
        "efforts": efforts(),
        "repos": repos(),
        "listening": listening(),
        "health": desk_health(),
        "incoming": [e for e in incoming.values() if incoming_shown(e)],
        "proposals": [p for p in proposals if p["state"] in SHOWN_PROPOSALS],
        "autostart": autostart_setting(),
        "spaces": spaces_setting(),
    }


def close_ask(item: dict) -> None:
    """Keep when the item's question was asked, answered on the board and cleared, with its kind."""
    if item.get("asks"):
        item.setdefault("askLog", []).append(
            {
                "kind": item["asks"].get("kind"),
                "asked": item["asks"]["at"],
                "answered": (item.get("answer") or {}).get("at"),
                "cleared": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            }
        )


def apply_status(item: dict, status: str) -> None:
    """Set an item's status and the fields that follow from it, leaving a new Next rank to the caller."""
    if item["status"] == "started" and status in ("open", "next"):
        item["paused"] = datetime.datetime.now().isoformat(timespec="seconds")
    elif status not in ("open", "next"):
        item.pop("paused", None)
        item.pop("unblocked", None)
    item["status"] = status
    item.pop("needs", None)
    close_ask(item)
    item.pop("asks", None)
    item.pop("answer", None)
    item["done"] = datetime.date.today().isoformat() if status in CLOSED_STATUSES else None
    if status not in CLOSED_STATUSES:
        item.pop("archived", None)
    if status != "next":
        item.pop("rank", None)
    if status in ("next", "requested"):
        item.pop("suggested", None)


def start_note(note: dict | None) -> dict | None:
    """The note and grants I gave on the board when starting an item."""
    text = (note or {}).get("text", "").strip()
    grants = {key: True for key in START_GRANTS if (note or {}).get(key)}
    if "babysit" in grants:
        grants["draft_pr"] = True
    if not text and not grants:
        return None
    return {"text": text, **grants, "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}


def set_status(ids: list[str], status: str, note: dict | None = None) -> None:
    if status not in SETTABLE_STATUSES:
        raise ValueError(status)
    items = all_items()
    for item_id in ids:
        item_path(item_id)
        if status == "requested" and open_blockers(items[item_id], items):
            raise ValueError(f"blocked: {items[item_id]['title']}")
    changes = []
    saved_note = start_note(note)
    next_rank = max((i.get("rank") or 0 for i in items.values() if i["status"] == "next"), default=0)
    for item_id in ids:
        item = items[item_id]
        old = item["status"]
        allowed = {"open", "next", "done"} if old == "started" else SETTABLE_STATUSES - ({"done"} if old == "new" else set())
        retry = status == "requested" and item.get("needs")
        if old == status and not retry or old == "done" or status not in allowed:
            continue
        apply_status(item, status)
        item.pop("adopted", None)
        if status == "requested" and old != "requested":
            item.pop("start_note", None)
            if saved_note:
                item["start_note"] = saved_note
        if status == "next":
            next_rank += 1
            item["rank"] = next_rank
        write_json(item_path(item_id), item)
        changes.append({"id": item_id, "from": old, "to": status})
    if changes:
        log_event({"type": "status", "changes": changes})


def slug_id(day: datetime.date, title: str) -> str:
    return f"{day:%Y%m%d}-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]


def free_path(base: str) -> Path:
    path = BACKLOG / f"{base}.json"
    n = 2
    while path.exists():
        path = BACKLOG / f"{base}-{n}.json"
        n += 1
    return path


def add_item(title: str, **fields: object) -> dict:
    """Write a new open item, named after today's date and its title, and return it."""
    today = datetime.date.today()
    path = free_path(slug_id(today, title))
    item = {
        "id": path.stem,
        "title": title,
        "repo": None,
        "effort": None,
        "kind": None,
        "label": None,
        "summary": "",
        "brief": "",
        "source": "unknown",
        "created": today.isoformat(),
        "status": "open",
        "thread": None,
        "pr": None,
        "done": None,
        "comments": [],
        **fields,
    }
    BACKLOG.mkdir(exist_ok=True)
    write_json(path, item)
    return item


def capture(text: str, repo: str | None, effort: str | None) -> None:
    text = text.strip()
    check_repo(repo)
    if not text:
        raise ValueError("empty capture")
    today = datetime.date.today()
    first_line = text.splitlines()[0]
    title = first_line if len(first_line) <= 80 else first_line[:77].rstrip() + "..."
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50] or "capture"
    base = f"{today:%Y%m%d}-{slug}"
    path = BACKLOG / f"{base}.json"
    n = 2
    while path.exists():
        path = BACKLOG / f"{base}-{n}.json"
        n += 1
    write_json(
        path,
        {
            "id": path.stem,
            "title": title,
            "repo": repo or None,
            "effort": effort or None,
            "kind": None,
            "label": None,
            "summary": "",
            "brief": text,
            "source": "me",
            "created": today.isoformat(),
            "status": "new",
            "thread": None,
            "pr": None,
            "done": None,
            "comments": [],
        },
    )
    log_event({"type": "capture", "id": path.stem})


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, data: object) -> None:
        self.send(status, json.dumps(data).encode(), "application/json")

    def remote(self) -> bool:
        return self.server.server_address[0] != "127.0.0.1"

    def allowed(self) -> bool:
        if not self.remote():
            port = self.server.server_address[1]
            return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")
        try:
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
        except CookieError:
            return False
        token = board_token()
        return bool(token) and COOKIE in cookie and hmac.compare_digest(cookie[COOKIE].value.encode(), token.encode())

    def login(self, code: str) -> None:
        try:
            expected = LOGIN.read_text().strip()
            valid = (
                bool(expected)
                and time.time() - LOGIN.stat().st_mtime < LOGIN_FOR
                and hmac.compare_digest(code.encode(), expected.encode())
            )
        except OSError:
            valid = False
        if not valid:
            self.send_json(403, {"error": "this login link is used or expired, run bin/board --login-url for a new one"})
            return
        LOGIN.unlink(missing_ok=True)
        self.send_response(303)
        self.send_header("Set-Cookie", f"{COOKIE}={board_token()}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax")
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        url = urlsplit(self.path)
        if self.remote() and url.path == "/login":
            self.login(parse_qs(url.query).get("code", [""])[0])
        elif not self.allowed():
            self.send_json(403, {"error": "forbidden"})
        elif url.path == "/":
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self.send_json(200, load_state())
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self.allowed() or self.headers.get("Content-Type") != "application/json":
            self.send_json(403, {"error": "forbidden"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        try:
            if self.path == "/api/capture":
                capture(body["text"], body.get("repo"), body.get("effort"))
            elif self.path == "/api/comment":
                path = item_path(body["id"])
                item = json.loads(path.read_text())
                item["comments"].append({"at": now, "by": "me", "text": body["text"]})
                write_json(path, item)
                log_event({"type": "comment", "id": body["id"]})
            elif self.path == "/api/status":
                set_status(body["ids"], body["status"], body.get("note"))
            elif self.path == "/api/ask":
                item = next(
                    (i for i in all_items().values() if i["thread"] == body["thread"] and i["status"] not in CLOSED_STATUSES),
                    None,
                )
                if item is None:
                    raise FileNotFoundError(f"no open item for thread {body['thread']}")
                close_ask(item)
                item.pop("answer", None)
                if body.get("text"):
                    item["asks"] = {
                        "text": body["text"],
                        "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                        **({"kind": body["kind"]} if body.get("kind") else {}),
                    }
                else:
                    item.pop("asks", None)
                write_json(item_path(item["id"]), item)
            elif self.path == "/api/answer":
                path = item_path(body["id"])
                item = json.loads(path.read_text())
                if not item.get("asks") or not body["text"].strip():
                    raise ValueError("no open question to answer")
                if body["to"] != item["asks"]["text"]:
                    raise ValueError("the question changed, read it again")
                item["answer"] = {
                    "text": body["text"].strip(),
                    "to": item["asks"]["text"],
                    "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                }
                write_json(path, item)
                log_event({"type": "answer", "id": body["id"]})
            elif self.path == "/api/adopt":
                path = item_path(body["id"])
                item = json.loads(path.read_text())
                if item.pop("adopted", None):
                    write_json(path, item)
                log_event({"type": "adopt", "id": body["id"]})
            elif self.path == "/api/archive":
                archived = []
                for item_id in body["ids"]:
                    path = item_path(item_id)
                    item = json.loads(path.read_text())
                    if item["status"] in CLOSED_STATUSES and not item.get("archived"):
                        item["archived"] = datetime.date.today().isoformat()
                        write_json(path, item)
                        archived.append(item_id)
                if archived:
                    log_event({"type": "archive", "ids": archived})
            elif self.path == "/api/order":
                for rank, item_id in enumerate(body["ids"], 1):
                    path = item_path(item_id)
                    item = json.loads(path.read_text())
                    if item["status"] == "next":
                        item["rank"] = rank
                        write_json(path, item)
            elif self.path == "/api/incoming/dismiss":
                with locked(INCOMING):
                    incoming = json.loads(INCOMING.read_text())
                    incoming[body["url"]]["status"] = "dismissed"
                    write_json(INCOMING, incoming)
                log_event({"type": "hide", "url": body["url"]})
            elif self.path == "/api/incoming/snooze":
                until = datetime.date.fromisoformat(body["until"]).isoformat()
                with locked(INCOMING):
                    incoming = json.loads(INCOMING.read_text())
                    incoming[body["url"]]["snoozed"] = until
                    write_json(INCOMING, incoming)
            elif self.path == "/api/incoming/chat":
                with locked(INCOMING):
                    incoming = json.loads(INCOMING.read_text())
                    incoming[body["url"]].setdefault("chat", []).append({"at": now, "by": "me", "text": body["text"]})
                    write_json(INCOMING, incoming)
                log_event({"type": "chat", "url": body["url"]})
            elif self.path == "/api/proposals/chat":
                with locked(PROPOSALS):
                    proposals = json.loads(PROPOSALS.read_text())
                    proposal = {p["id"]: p for p in proposals}[body["id"]]
                    proposal.setdefault("chat", []).append({"at": now, "by": "me", "text": body["text"]})
                    write_json(PROPOSALS, proposals)
                log_event({"type": "chat", "id": body["id"]})
            elif self.path == "/api/proposals":
                if body["decision"] not in ("approve", "dismiss"):
                    raise ValueError(body["decision"])
                with locked(PROPOSALS):
                    proposals = json.loads(PROPOSALS.read_text())
                    chosen = [p for p in proposals if p["id"] in body["ids"] and p["state"] in SHOWN_PROPOSALS]
                    for p in chosen:
                        p["state"] = "approved" if body["decision"] == "approve" else "dismissed"
                        p.pop("error", None)
                    write_json(PROPOSALS, proposals)
                if chosen:
                    log_event({"type": "apply" if body["decision"] == "approve" else "dismiss", "ids": [p["id"] for p in chosen]})
            elif self.path == "/api/autostart":
                known = {e["slug"] for e in efforts()}
                if body["mode"] not in AUTOSTART_MODES:
                    raise ValueError(f"unknown mode {body['mode']}")
                chosen = sorted(set(body["efforts"]) & known)
                write_json(AUTOSTART, {"mode": body["mode"], "efforts": chosen, "reviews": bool(body["reviews"])})
                log_event({"type": "autostart"})
            elif self.path == "/api/spaces":
                change_spaces(body)
            elif self.path == "/api/update":
                known = {e["slug"] for e in efforts()}
                fields = {k: (v or None) for k, v in body["fields"].items() if k in ("effort", "repo")}
                if fields.get("effort") and fields["effort"] not in known:
                    raise ValueError(f"unknown effort {fields['effort']}")
                check_repo(fields.get("repo"))
                if "blockedBy" in body["fields"]:
                    blockers = body["fields"]["blockedBy"]
                    if not isinstance(blockers, list) or not all(isinstance(b, str) and b.strip() for b in blockers):
                        raise ValueError("blockedBy must be a list of item ids or notes")
                    fields["blockedBy"] = [b.strip() for b in blockers]
                for item_id in body["ids"]:
                    path = item_path(item_id)
                    item = json.loads(path.read_text())
                    item.update(fields)
                    if "blockedBy" in fields:
                        item.pop("unblocked", None)
                    write_json(path, item)
            else:
                self.send_json(404, {"error": "not found"})
                return
        except (KeyError, ValueError, FileNotFoundError) as err:
            self.send_json(400, {"error": str(err)})
            return
        self.send_json(200, load_state())


def serve_tailnet(address: str, port: int) -> None:
    """Serve on the tailnet address once it exists, since Tailscale may connect after the board starts."""
    waited = False
    while True:
        try:
            server = ThreadingHTTPServer((address, port), Handler)
        except OSError as err:
            if not waited:
                print(f"waiting for {address} to come up: {err}", file=sys.stderr, flush=True)
                waited = True
            time.sleep(30)
            continue
        server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--login-url", action="store_true", help="print a link that lets one browser on the tailnet in, once")
    args = parser.parse_args()
    address = tailnet_address()
    if args.login_url:
        if not address:
            sys.exit(f"set tailnet in {BOARD_CONFIG} first")
        print(login_url(address, args.port))
        return
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    if address:
        board_token()
        threading.Thread(target=serve_tailnet, args=(address, args.port), daemon=True).start()
    print(f"http://127.0.0.1:{args.port}" + (f" and http://{address}:{args.port}" if address else ""))
    server.serve_forever()


if __name__ == "__main__":
    main()
