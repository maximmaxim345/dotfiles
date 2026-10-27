#!/usr/bin/env python3
"""Serve the desk board on localhost."""

from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import json
import os
import re
import sqlite3
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from urllib.parse import urlsplit

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
SETTABLE_STATUSES = {"open", "next", "requested", "done", "dropped"}
CLOSED_STATUSES = {"done", "dropped"}


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


def log_event(event: dict) -> None:
    STATE.mkdir(exist_ok=True)
    event["at"] = datetime.datetime.now().isoformat(timespec="seconds")
    with EVENTS.open("a") as f:
        f.write(json.dumps(event) + "\n")


def open_blockers(item: dict, items: dict[str, dict]) -> list[str]:
    return [b for b in item.get("blockedBy") or [] if b not in items or items[b]["status"] not in CLOSED_STATUSES]


def all_items() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(BACKLOG.glob("*.json"))}


def load_state() -> dict:
    items = list(all_items().values())
    threads = json.loads(THREADS.read_text()) if THREADS.exists() else None
    return {"items": items, "threads": threads, "efforts": efforts(), "repos": repos(), "listening": listening()}


def apply_status(item: dict, status: str) -> None:
    """Set an item's status and the fields that follow from it, leaving a new Next rank to the caller."""
    item["status"] = status
    item.pop("needs", None)
    item.pop("asks", None)
    item["done"] = datetime.date.today().isoformat() if status in CLOSED_STATUSES else None
    if status not in CLOSED_STATUSES:
        item.pop("archived", None)
    if status != "next":
        item.pop("rank", None)
    if status in ("next", "requested"):
        item.pop("suggested", None)


def set_status(ids: list[str], status: str) -> None:
    if status not in SETTABLE_STATUSES:
        raise ValueError(status)
    items = all_items()
    for item_id in ids:
        item_path(item_id)
        if status == "requested" and open_blockers(items[item_id], items):
            raise ValueError(f"blocked: {items[item_id]['title']}")
    changes = []
    next_rank = max((i.get("rank") or 0 for i in items.values() if i["status"] == "next"), default=0)
    for item_id in ids:
        item = items[item_id]
        old = item["status"]
        allowed = {"open", "next", "done"} if old == "started" else SETTABLE_STATUSES - ({"done"} if old == "new" else set())
        retry = status == "requested" and item.get("needs")
        if old == status and not retry or old == "done" or status not in allowed:
            continue
        apply_status(item, status)
        if status == "next":
            next_rank += 1
            item["rank"] = next_rank
        write_json(item_path(item_id), item)
        changes.append({"id": item_id, "from": old, "to": status})
    if changes:
        log_event({"type": "status", "changes": changes})


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

    def local_host(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def do_GET(self) -> None:
        if not self.local_host():
            self.send_json(403, {"error": "forbidden"})
        elif urlsplit(self.path).path == "/":
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self.send_json(200, load_state())
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self.local_host() or self.headers.get("Content-Type") != "application/json":
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
                set_status(body["ids"], body["status"])
            elif self.path == "/api/ask":
                item = next(
                    (i for i in all_items().values() if i["thread"] == body["thread"] and i["status"] not in CLOSED_STATUSES),
                    None,
                )
                if item is None:
                    raise FileNotFoundError(f"no open item for thread {body['thread']}")
                if body.get("text"):
                    item["asks"] = {
                        "text": body["text"],
                        "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                    }
                else:
                    item.pop("asks", None)
                write_json(item_path(item["id"]), item)
            elif self.path == "/api/adopt":
                item_path(body["id"])
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
                    write_json(path, item)
            else:
                self.send_json(404, {"error": "not found"})
                return
        except (KeyError, ValueError, FileNotFoundError) as err:
            self.send_json(400, {"error": str(err)})
            return
        self.send_json(200, load_state())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
