"""Serve registered review pages, keep what I mark on them, and send my answer to the thread that registered them."""

from __future__ import annotations

import contextlib
import datetime
import fcntl
import hashlib
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
KIT_DATA = re.compile(rb'<script id="kit-data" type="application/json">(.*?)</script>', re.S)
DRAFT_STATUSES = ("post", "lower", "dismissed")
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


def page_data(body: bytes) -> dict:
    match = KIT_DATA.search(body)
    try:
        data = json.loads(match[1]) if match else {}
    except json.JSONDecodeError:
        data = {}
    return data if isinstance(data, dict) else {}


def digest(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def narrative_of(data: dict) -> dict | None:
    review = data.get("review")
    if not isinstance(review, dict):
        return None
    drafts = {d["id"]: digest(d["text"]) for d in review["drafts"]}
    return {"version": review["version"], "drafts": drafts, "body": digest(review["body"])}


def page_file(review: dict) -> Path:
    page = Path(review["page"])
    if page.suffix != ".html" or not page.is_file():
        raise FileNotFoundError(f"the page of review {review['id']} is gone")
    return page


# Draft and body edits carry over while the narrative's text they started from stays the same.
def carried(review: dict, new: dict | None) -> dict:
    state = review["state"]
    old = review.get("narrative") or {"drafts": {}, "body": None}
    kept = {k: v for k, v in state.items() if k not in ("drafts", "body")}
    kept["drafts"] = {}
    if new:
        kept["drafts"] = {i: e for i, e in state.get("drafts", {}).items() if old["drafts"].get(i, "") == new["drafts"].get(i)}
        if "body" in state and old["body"] == new["body"]:
            kept["body"] = state["body"]
    return kept


# A rebuilt page has other hunks, so what was marked on the old one is set aside and ids keep counting.
def renew(review: dict, body: bytes) -> None:
    data = page_data(body)
    key = str(data.get("key", ""))
    new = narrative_of(data)
    if review["key"] == key:
        if new != review.get("narrative"):
            review.update(state=carried(review, new), narrative=new)
            review["rev"] += 1
        return
    state = review["state"]
    if state["comments"] or review["replies"] or state.get("drafts") or "body" in state:
        review.setdefault("earlier", []).append({k: review[k] for k in ("key", "state", "replies", "sent")})
    review.update(
        key=key,
        state={**carried(review, new), "comments": [], "picks": {}, "notes": {}, "resolved": []},
        scroll=0,
        replies={},
        sent={"comments": [], "picks": {}, "notes": {}},
        narrative=new,
    )
    review["rev"] += 1


def check_page(review: dict, body: dict) -> None:
    narrative = review.get("narrative")
    if body.get("page") != review["key"] or (narrative and body.get("version") != narrative["version"]):
        raise Stale("this page was rebuilt")


def register(page: Path, thread: str) -> str:
    page = page.resolve()
    if page.suffix != ".html" or not page.is_file():
        raise ValueError(f"{page} is not an HTML file")
    if not thread.strip():
        raise ValueError("the thread id is empty")
    body = page.read_bytes()
    with lock("register"):
        for path in REVIEWS.glob("*.json"):
            review = json.loads(path.read_text())
            if review["page"] == str(page):
                with changing(review["id"]) as review:
                    review["thread"] = thread
                    renew(review, body)
                return str(review["id"])
        review_id = secrets.token_urlsafe(12)
        review = {"id": review_id, "page": str(page), "thread": thread, "registered": now(), "rev": 0, "key": None}
        review["state"] = {"nextId": 1, "comments": []}
        review["replies"] = {}
        renew(review, body)
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
    text = (
        f"Answer from the review page {Path(review['page']).name} (review {review['id']}). Reply to each [n] comment"
        f" with `~/desk/bin/review-page reply {review['id']} --comment <n> --text-file <file>`."
    )
    if review.get("narrative"):
        text += (
            f" Run `~/desk/bin/review-page export {review['id']}` for every draft's final text and status,"
            " the review body and the picks."
        )
    return text


def shown(review: dict) -> dict:
    keys = ("key", "rev", "state", "scroll", "replies", "sent")
    version = (review.get("narrative") or {}).get("version")
    return {**{key: review[key] for key in keys}, "version": version, "send": bool(review["thread"]), "header": header(review)}


def text_of(body: dict, name: str) -> str:
    value = body[name]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is empty")
    return value


def edit(review_id: str, body: dict) -> dict:
    op = body["op"]
    with changing(review_id) as review:
        check_page(review, body)
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
        elif op == "draft":
            if review.get("narrative") is None or body["id"] not in review["narrative"]["drafts"]:
                raise ValueError(f"the page has no draft {body['id']}")
            change = {k: body[k] for k in ("text", "status", "reason") if k in body}
            if not change or not all(isinstance(v, str) for v in change.values()):
                raise ValueError("a draft change sets text, status or reason as text")
            if change.get("status", "post") not in DRAFT_STATUSES:
                raise ValueError(f"a draft status is one of {', '.join(DRAFT_STATUSES)}")
            state.setdefault("drafts", {}).setdefault(body["id"], {}).update(change)
        elif op == "body":
            if not isinstance(body["value"], str):
                raise ValueError("the review body is not a string")
            state["body"] = body["value"]
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
        check_page(review, body)
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


def export(review_id: str) -> dict:
    with changing(review_id) as review:
        page = page_file(review).read_bytes()
        renew(review, page)
    data = page_data(page)
    pr = data.get("review")
    if not isinstance(pr, dict):
        raise ValueError(f"review {review_id} is not a PR review page")
    state = review["state"]
    drafts = []
    for draft in pr["drafts"]:
        edit = state.get("drafts", {}).get(draft["id"], {})
        final = {**draft, **edit}
        out = {k: final[k] for k in ("id", "status", "path", "line", "side", "text", "where", "proof")}
        out["in_diff"] = draft["inDiff"]
        out["edited"] = any(final[k] != draft[k] for k in ("text", "status"))
        if final.get("reason"):
            out["reason"] = final["reason"]
        drafts.append(out)
    roots = [c for c in state["comments"] if not c.get("parent")]
    return {
        "review": review_id,
        "page": review["page"],
        "pr": pr["url"],
        "head": pr["head"],
        "body": state.get("body", pr["body"]),
        "body_edited": state.get("body", pr["body"]) != pr["body"],
        "drafts": drafts,
        "picks": {**data.get("picks", {}), **state["picks"]},
        "notes": {k: v for k, v in state["notes"].items() if v.strip()},
        "comments": [{k: c[k] for k in ("id", "label", "text")} for c in roots],
    }


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
                renew(review, body)
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
