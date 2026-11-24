"""Serve registered review pages, keep what I mark on them, and send my answer to the thread that registered them."""

from __future__ import annotations

import contextlib
import datetime
import fcntl
import json
import os
import re
import secrets
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Iterator

REVIEWS = Path.home() / "desk" / "state" / "reviews"
T3 = Path.home() / ".t3" / "bin" / "t3"
REVIEW_ID = re.compile(r"[A-Za-z0-9_-]{8,32}")
KIT_KEY = re.compile(rb'<script id="kit-data" type="application/json">\{"key": "([0-9a-f]+)"')
LONGEST_ANSWER = 200_000
PAGE_POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'"
)


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def write(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


@contextlib.contextmanager
def lock(name: str) -> Iterator[None]:
    REVIEWS.mkdir(parents=True, exist_ok=True)
    with open(REVIEWS / f"{name}.lock", "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def review_path(review_id: str) -> Path:
    path = REVIEWS / f"{review_id}.json"
    if not REVIEW_ID.fullmatch(review_id) or not path.exists():
        raise FileNotFoundError(f"no review page {review_id}")
    return path


def load(review_id: str) -> dict:
    return json.loads(review_path(review_id).read_text())


@contextlib.contextmanager
def changing(review_id: str) -> Iterator[dict]:
    with lock(review_id):
        review = load(review_id)
        yield review
        write(review_path(review_id), review)


class Stale(Exception):
    pass


def page_key(body: bytes) -> str:
    match = KIT_KEY.search(body)
    return match[1].decode() if match else ""


def page_file(review: dict) -> Path:
    page = Path(review["page"])
    if page.suffix != ".html" or not page.is_file():
        raise FileNotFoundError(f"the page of review {review['id']} is gone")
    return page


# A rebuilt page has other hunks, so what was marked on the old one is set aside and ids keep counting.
def renew(review: dict, key: str) -> None:
    if review["key"] == key:
        return
    if review["state"]["comments"] or review["replies"]:
        review.setdefault("earlier", []).append({k: review[k] for k in ("key", "state", "replies", "sent")})
    review.update(
        key=key,
        state={"comments": [], "picks": {}, "notes": {}, "resolved": [], "nextId": review["state"]["nextId"]},
        scroll=0,
        replies={},
        sent={"comments": [], "picks": {}, "notes": {}},
    )
    review["rev"] += 1


def register(page: Path, thread: str) -> str:
    page = page.resolve()
    if page.suffix != ".html" or not page.is_file():
        raise ValueError(f"{page} is not an HTML file")
    if not thread.strip():
        raise ValueError("the thread id is empty")
    key = page_key(page.read_bytes())
    with lock("register"):
        for path in REVIEWS.glob("*.json"):
            review = json.loads(path.read_text())
            if review["page"] == str(page):
                with changing(review["id"]) as review:
                    review["thread"] = thread
                    renew(review, key)
                return str(review["id"])
        review_id = secrets.token_urlsafe(12)
        review = {"id": review_id, "page": str(page), "thread": thread, "registered": now(), "rev": 0, "key": None}
        review["state"] = {"nextId": 1, "comments": []}
        review["replies"] = {}
        renew(review, key)
        write(REVIEWS / f"{review_id}.json", review)
    return review_id


def reply(review_id: str, comment: int, text: str) -> None:
    if not text.strip():
        raise ValueError("the reply is empty")
    with changing(review_id) as review:
        roots = {c["id"] for c in review["state"]["comments"] if not c.get("parent")}
        if comment not in roots:
            raise ValueError(f"the page has no comment [{comment}]")
        review["replies"].setdefault(str(comment), []).append({"text": text.strip(), "at": now()})
        review["rev"] += 1


def header(review: dict) -> str:
    return (
        f"Answer from the review page {Path(review['page']).name} (review {review['id']}). Reply to each [n] comment"
        f" with `~/desk/bin/review-page reply {review['id']} --comment <n> --text-file <file>`."
    )


def shown(review: dict) -> dict:
    keys = ("key", "rev", "state", "scroll", "replies", "sent")
    return {**{key: review[key] for key in keys}, "send": bool(review["thread"]), "header": header(review)}


def text_of(body: dict, name: str) -> str:
    value = body[name]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is empty")
    return value


def edit(review_id: str, body: dict) -> dict:
    op = body["op"]
    with changing(review_id) as review:
        if body.get("page") != review["key"]:
            raise Stale("this page was rebuilt")
        state = review["state"]
        if op == "scroll":
            review["scroll"] = int(body["y"])
            return shown(review)
        if op == "add":
            comment = {"id": state["nextId"], "hunk": body["hunk"], "key": text_of(body, "key")}
            comment.update(label=text_of(body, "label"), text=text_of(body, "text").strip(), at=now())
            if comment["hunk"] is not None and not isinstance(comment["hunk"], str):
                raise ValueError("hunk is not a string")
            if body.get("parent"):
                if body["parent"] not in {c["id"] for c in state["comments"] if not c.get("parent")}:
                    raise ValueError(f"the page has no comment [{body['parent']}]")
                comment["parent"] = body["parent"]
            state["comments"].append(comment)
            state["nextId"] += 1
        elif op == "remove":
            if body["id"] in review["sent"]["comments"]:
                raise ValueError("a sent comment stays")
            state["comments"] = [c for c in state["comments"] if c["id"] != body["id"]]
        elif op in ("pick", "note"):
            value = body["value"]
            if not isinstance(value, str):
                raise ValueError(f"the {op} is not a string")
            state["picks" if op == "pick" else "notes"][str(body["call"])] = value
        elif op == "resolve":
            state["resolved"] = [i for i in state["resolved"] if i != body["id"]] + ([body["id"]] if body["on"] else [])
        elif op == "clear":
            state["comments"] = [c for c in state["comments"] if c["id"] in review["sent"]["comments"]]
            state["picks"], state["notes"] = {}, {}
        else:
            raise ValueError(f"unknown change {op}")
        review["rev"] += 1
    return shown(review)


def send(review_id: str, body: dict, deliver: bool = True) -> dict:
    text = body["text"]
    if not isinstance(text, str) or not text.strip() or len(text) > LONGEST_ANSWER:
        raise ValueError("the answer is empty or too long")
    comments, picks, notes = {int(c) for c in body["comments"]}, dict(body["picks"]), dict(body["notes"])
    with changing(review_id) as review:
        if body.get("page") != review["key"]:
            raise Stale("this page was rebuilt")
        if deliver:
            message = f"{header(review)}\n\n{text.strip()}"
            try:
                result = subprocess.run(
                    [str(T3), "thread", "send", review["thread"], message], capture_output=True, text=True, timeout=60
                )
            except (OSError, subprocess.TimeoutExpired) as err:
                raise RuntimeError(str(err)) from err
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or f"t3 exited with {result.returncode}")
        sent = review["sent"]
        sent["comments"] = sorted(set(sent["comments"]) | comments)
        sent["picks"] = picks
        sent["notes"] = notes
        sent["at"] = now()
        review["rev"] += 1
    return shown(review)


def answer(handler: BaseHTTPRequestHandler, status: int, data: object) -> None:
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def get(handler: BaseHTTPRequestHandler, path: str) -> None:
    try:
        page = re.fullmatch(r"/review/([^/]+)", path)
        if page:
            with changing(page[1]) as review:
                body = page_file(review).read_bytes()
                renew(review, page_key(body))
            handler.send_response(200)
            handler.send_header("Content-Type", "text/html; charset=utf-8")
            handler.send_header("Content-Length", str(len(body)))
            handler.send_header("Cache-Control", "no-store")
            handler.send_header("Content-Security-Policy", PAGE_POLICY)
            handler.end_headers()
            handler.wfile.write(body)
            return
        state = re.fullmatch(r"/api/review/([^/]+)/state", path)
        if not state:
            raise FileNotFoundError(path)
        answer(handler, 200, shown(load(state[1])))
    except FileNotFoundError as err:
        answer(handler, 404, {"error": str(err)})


def post(handler: BaseHTTPRequestHandler, path: str, body: dict) -> None:
    match = re.fullmatch(r"/api/review/([^/]+)/(edit|send|sent)", path)
    try:
        if not match:
            raise FileNotFoundError(path)
        data = edit(match[1], body) if match[2] == "edit" else send(match[1], body, deliver=match[2] == "send")
        answer(handler, 200, data)
    except FileNotFoundError as err:
        answer(handler, 404, {"error": str(err)})
    except Stale as err:
        answer(handler, 409, {"error": str(err)})
    except (KeyError, TypeError, ValueError) as err:
        answer(handler, 400, {"error": str(err)})
    except RuntimeError as err:
        answer(handler, 502, {"error": f"sending failed: {err}"})
