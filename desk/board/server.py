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

import reviews

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
PREREADS = STATE / "prereads.json"
PROPOSALS = STATE / "proposals.json"
AUTOSTART = STATE / "autostart.json"
AUTOSTART_MODES = {"off", "focus", "all"}
AUTOSTART_LAST = STATE / "autostart-last.json"
SPACES = STATE / "spaces.json"
DEFAULT_SPACE = "work"
SPACE_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,30}")
SHOWN_INCOMING = {"new", "needs-you", "waiting"}
CHAT_SHOWN_FOR = datetime.timedelta(days=1)
SHOWN_PROPOSALS = {"open", "approved", "failed"}
SETTABLE_STATUSES = {"open", "requested", "done", "dropped"}
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
TODAY = STATE / "today.json"
BUDGET = STATE / "budget.json"
DEFAULT_BUDGET = 240
SIZE_MINUTES = {"S": 10, "M": 20, "L": 40}
ASK_MINUTES = {"decide": 5, "review": 20, "push": 5, "post": 5, "device-test": 30, "question": 10}
OTHER_MINUTES = {"start": 5, "reply": 10, "failed": 5, "worktree": 5, "desk": 10}
KIND_MINUTES = {"bugfix": 15, "feature": 20, "review": 15, "design": 30, "test": 10, "docs": 10}
NOW_GROUPS = ("act", "unblock", "land", "decide")
UNBLOCK_KINDS = {"reply", "start", "failed"}
LAND_KINDS = {"review", "push", "post", "device-test"}
PLACES = ("today", "later")
SAMPLES_NEEDED = 5
LONGEST_SAMPLE = 120
LABEL_ORDER = {"user-visible bug": 0, "reachable but rare": 1}
WORKTREES = STATE / "worktrees.json"
GOALS = DESK / "goals"
PARKED_AFTER = datetime.timedelta(days=14)
FATES = ("keep", "start", "drop")
MILESTONE = re.compile(r"([a-z0-9][a-z0-9-]*)#([1-9][0-9]*)")


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

        def failed_in_a_row(thread: str) -> int:
            statuses = conn.execute(
                "SELECT status FROM orchestration_v2_projection_runs WHERE thread_id = ?"
                " AND status IN ('completed', 'failed', 'cancelled', 'interrupted') ORDER BY ordinal DESC LIMIT 50",
                (thread,),
            ).fetchall()
            return next((n for n, (status,) in enumerate(statuses) if status != "failed"), len(statuses))

        failed = failed_in_a_row(row[0])
        routines = conn.execute(
            "SELECT thread_id, title FROM orchestration_v2_projection_threads"
            " WHERE project_id = ? AND title LIKE 'routine - %' AND archived_at IS NULL AND deleted_at IS NULL",
            (project,),
        ).fetchall()
        broken = [
            {"thread": t, "title": title, "failed": n} for t, title in routines if (n := failed_in_a_row(t)) >= FAILED_IN_A_ROW
        ]
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
    swept = datetime.datetime.fromisoformat(last_sweep.replace("Z", "+00:00")) if last_sweep else None
    due = last_sweep_due(datetime.datetime.now().astimezone())
    return {
        "thread": row[0],
        "failed": failed if failed >= FAILED_IN_A_ROW else 0,
        "lastSweep": swept.astimezone().isoformat(timespec="minutes") if swept else None,
        "sweepStale": swept is None or swept < due - SWEEP_EARLY,
        "routines": broken,
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


def in_window(now: datetime.datetime) -> bool:
    return now.weekday() < 5 and 8 <= now.hour < 20


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
    by_id = all_items()
    threads = json.loads(THREADS.read_text()) if THREADS.exists() else None
    incoming = json.loads(INCOMING.read_text()) if INCOMING.exists() else {}
    proposals = json.loads(PROPOSALS.read_text()) if PROPOSALS.exists() else []
    shown = [e for e in incoming.values() if incoming_shown(e)]
    health = desk_health()
    worktrees = json.loads(WORKTREES.read_text()) if WORKTREES.exists() else {}
    day = plan_day(by_id, threads or {}, shown, health, worktrees)
    return {
        "items": [{**item, "estimate": item_minutes(item)} for item in by_id.values()],
        "threads": threads,
        "efforts": efforts(),
        "repos": repos(),
        "listening": listening(),
        "health": health,
        "incoming": shown,
        "proposals": [p for p in proposals if p["state"] in SHOWN_PROPOSALS],
        "prereadError": (json.loads(PREREADS.read_text()) if PREREADS.exists() else {}).get("error"),
        "autostart": autostart_setting(),
        "autostartLast": json.loads(AUTOSTART_LAST.read_text()) if AUTOSTART_LAST.exists() else None,
        "spaces": spaces_setting(),
        "now": day["now"],
        "today": {key: day[key] for key in ("date", "budget", "waiting", "rows")},
        "askMinutes": ask_minutes(list(by_id.values())),
        "worktrees": worktrees,
        "goals": load_goals(list(by_id.values())),
        "parked": [i for i, item in by_id.items() if parked(item, by_id) and i not in day["moves"]],
    }


def close_ask(item: dict) -> None:
    """Keep when the item's question was asked, answered on the board and cleared, with its kind."""
    if item.get("asks"):
        item.setdefault("askLog", []).append(
            {
                "kind": item["asks"].get("kind"),
                "asked": item["asks"]["at"],
                "opened": item["asks"].get("opened"),
                "answered": (item.get("answer") or {}).get("at"),
                "cleared": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            }
        )


def parse_time(value: str) -> datetime.datetime:
    """Read an ISO date or time, taking times without a zone as local."""
    moment = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.astimezone()


def item_minutes(item: dict) -> int:
    """My minutes for the item, guessed from its kind, PR and thread when it has no size."""
    if item.get("minutes") or item.get("size"):
        return item.get("minutes") or SIZE_MINUTES[item["size"]]
    return 10 if item.get("pr") else 15 if item.get("thread") else KIND_MINUTES.get(item.get("kind") or "", 15)


def answer_times(item: dict) -> Iterator[tuple[str, float]]:
    """Per answered question of the item: its kind and my minutes from opening it on the board to answering."""
    for entry in item.get("askLog") or []:
        end = entry.get("answered") or entry.get("cleared")
        if not entry.get("opened") or not end:
            continue
        minutes = (parse_time(end) - parse_time(entry["opened"])).total_seconds() / 60
        if 0 <= minutes <= LONGEST_SAMPLE:
            yield entry.get("kind") or "question", minutes


def ask_minutes(items: list[dict]) -> dict[str, dict]:
    """Per ask kind: the default, my measured minutes and the estimate the board uses."""
    samples: dict[str, list[float]] = {kind: [] for kind in ASK_MINUTES}
    for item in items:
        for kind, minutes in answer_times(item):
            samples.setdefault(kind, []).append(minutes)
    result = {}
    for kind, found in samples.items():
        found.sort()
        median = round((found[(len(found) - 1) // 2] + found[len(found) // 2]) / 2) if found else None
        default = ASK_MINUTES.get(kind, ASK_MINUTES["question"])
        used = max(1, median) if median is not None and len(found) >= SAMPLES_NEEDED else default
        result[kind] = {"default": default, "samples": len(found), "median": median, "minutes": used}
    return result


def load_goals(items: list[dict]) -> list[dict]:
    """Each goal file, with my measured minutes per milestone added as `spent`."""
    spent: dict[str, float] = {}
    for item in items:
        if MILESTONE.fullmatch(item.get("parent") or ""):
            spent[item["parent"]] = spent.get(item["parent"], 0) + sum(m for _, m in answer_times(item))
    goals = []
    for path in sorted(GOALS.glob("*.json")) if GOALS.exists() else []:
        goal = json.loads(path.read_text())
        for n, milestone in enumerate(goal.get("milestones") or [], 1):
            milestone["spent"] = round(spent.get(f"{goal['slug']}#{n}", 0))
        goals.append(goal)
    return goals


def now_rows(
    items: dict[str, dict], threads: dict, incoming: list[dict], health: dict | None, worktrees: dict, spaces: dict
) -> list[dict]:
    """What waits on me, the row to do first on top."""
    estimates = ask_minutes(list(items.values()))
    snoozed = {t["thread"] for t in threads.get("snoozed") or []}
    rows = []

    def add(
        tier: int, kind: str, minutes: int, title: str, text: str, at: str | None, estimated: bool = True, **extra: object
    ) -> None:
        row = {"tier": tier, "kind": kind, "minutes": minutes, "title": title, "text": text, "at": at, **extra}
        rows.append({**row, "estimated": estimated, "group": now_group(row, items)})

    if health and (health["failed"] or health["sweepStale"]):
        add(0, "desk", OTHER_MINUTES["desk"], "The desk is not running", "", None, thread=health.get("thread"))

    def links(entry: dict) -> dict:
        return {key: entry.get(key) for key in ("item", "effort", "thread", "pr")}

    covered = set()
    for item in items.values():
        base = {"item": item["id"], "effort": item.get("effort"), "thread": item.get("thread"), "pr": item.get("pr")}
        if item["status"] == "requested" and item.get("needs"):
            add(2, "start", OTHER_MINUTES["start"], item["title"], item["needs"], item.get("paused"), **base)
        elif item["status"] == "started" and item.get("asks") and item.get("thread") not in snoozed:
            covered.add(item.get("thread"))
            if not item.get("answer"):
                kind = item["asks"].get("kind") or "question"
                minutes = item["asks"].get("minutes") or estimates.get(kind, estimates["question"])["minutes"]
                add(
                    1 if item.get("urgent") else 2,
                    kind,
                    minutes,
                    item["title"],
                    item["asks"]["text"],
                    item["asks"]["at"],
                    estimated=not item["asks"].get("minutes"),
                    **base,
                )
    for entry in threads.get("needsYou") or []:
        if entry["thread"] not in covered:
            kind = "review" if entry["title"].startswith("review: ") else "question"
            add(2, kind, estimates[kind]["minutes"], entry["title"], entry["why"], entry.get("since"), **links(entry))
    for entry in threads.get("failed") or []:
        add(2, "failed", OTHER_MINUTES["failed"], entry["title"], entry["why"], entry.get("since"), **links(entry))
    off = set(spaces["off"])
    waiting = [
        e
        for e in incoming
        if e["status"] == "needs-you"
        and (e.get("chat") or [{}])[-1].get("by") != "me"
        and space_of(e.get("effort"), spaces) not in off
    ]
    for entry in (e for e in waiting if e.get("preread")):
        add(
            1,
            "review",
            entry["preread"]["minutes"],
            entry["title"],
            entry.get("action") or "",
            entry.get("updated"),
            estimated=False,
            url=entry["url"],
            pr=entry["url"],
            effort=entry.get("effort"),
        )
    for entry in (e for e in waiting if not e.get("preread")):
        add(
            1,
            "reply",
            OTHER_MINUTES["reply"],
            entry["title"],
            entry.get("action") or "",
            entry.get("updated"),
            url=entry["url"],
            pr=entry["url"],
            effort=entry.get("effort"),
        )
    for entry in worktrees.get("held") or []:
        add(
            3,
            "worktree",
            OTHER_MINUTES["worktree"],
            entry["title"],
            entry["reason"],
            worktrees.get("at"),
            path=entry["path"],
            thread=entry["thread"],
        )
    rows = [r for r in rows if r["kind"] == "reply" or space_of(r.get("effort"), spaces) not in off]
    rows.sort(key=lambda r: (NOW_GROUPS.index(r["group"]), r["tier"], r["minutes"], r["at"] or ""))
    return rows


def now_group(row: dict, items: dict[str, dict]) -> str:
    if row["kind"] == "desk" or items.get(row.get("item") or "", {}).get("urgent"):
        return "act"
    if row["kind"] in UNBLOCK_KINDS:
        return "unblock"
    return "land" if row["kind"] in LAND_KINDS else "decide"


def last_touched(item: dict, items: dict[str, dict]) -> str:
    """The day of the item's last comment, answer, question, pause, unblock or keep, or of its creation."""
    asks, answer = item.get("asks") or {}, item.get("answer") or {}
    dates = [item["created"], item.get("paused"), item.get("unblocked"), item.get("kept"), asks.get("at"), answer.get("at")]
    blockers = [items[b].get("done") for b in item.get("blockedBy") or [] if b in items]
    return max(d[:10] for d in dates + blockers + [c["at"] for c in item["comments"]] if d)


def parked(item: dict, items: dict[str, dict]) -> bool:
    if item["status"] != "open" or item.get("thread") or item.get("urgent") or item.get("suggested"):
        return False
    return not open_blockers(item, items) and last_touched(item, items) <= (datetime.date.today() - PARKED_AFTER).isoformat()


def priority(item: dict) -> tuple:
    return (
        not item.get("urgent"),
        not item.get("suggested"),
        LABEL_ORDER.get(item.get("label") or "", len(LABEL_ORDER)),
        not item.get("seen"),
        item["created"],
        item["id"],
    )


def today_plan(items: dict[str, dict]) -> dict:
    """Today's moves, keeping the rows I moved onto an earlier day that are still open, and my old Next column."""
    day = datetime.date.today().isoformat()
    STATE.mkdir(exist_ok=True)
    with locked(TODAY):
        old = json.loads(TODAY.read_text()) if TODAY.exists() else {}
        nexts = sorted((i for i in items.values() if i["status"] == "next"), key=lambda i: i.get("rank") or 0)
        if old.get("date") == day and not nexts:
            return {"date": day, "moves": old.get("moves") or {}}
        moves = old.get("moves") or {}
        if old.get("date") != day:
            moves = {i: to for i, to in moves.items() if to == "today" and items.get(i, {}).get("status") == "open"}
        for item in nexts:
            note = (
                f"Moved from my Next column (rank {item.get('rank')}) onto my Today list, since the board has no Next column now."
            )
            apply_status(item, "open")
            item["comments"].append({"at": datetime.datetime.now().isoformat(timespec="seconds"), "by": "desk", "text": note})
            write_json(item_path(item["id"]), item)
            moves[item["id"]] = "today"
        plan = {"date": day, "moves": moves}
        write_json(TODAY, plan)
    return plan


def place_today(item_id: str, to: str | None) -> None:
    """Move an item above or below my Today line, or back to where the plan puts it."""
    if to not in (*PLACES, None):
        raise ValueError(f"unknown place {to}")
    item_path(item_id)
    plan = today_plan(all_items())
    with locked(TODAY):
        plan["moves"].pop(item_id, None)
        if to:
            plan["moves"][item_id] = to
        write_json(TODAY, plan)


def plan_changed() -> None:
    if autostart_setting()["mode"] != "off":
        log_event({"type": "today"})


def budget() -> int:
    return json.loads(BUDGET.read_text())["minutes"] if BUDGET.exists() else DEFAULT_BUDGET


def today_rows(items: dict[str, dict], plan: dict, minutes: int, waiting: int, spaces: dict) -> list[dict]:
    """The items I could start, above the line my moves, urgent items and then the budget draw, the rest below."""
    moves = plan.get("moves") or {}

    def startable(item: dict) -> bool:
        if item["status"] != "open" or item.get("needs") or open_blockers(item, items):
            return False
        return space_of(item.get("effort"), spaces) not in spaces["off"] and (item["id"] in moves or not parked(item, items))

    ready = sorted(filter(startable, items.values()), key=priority)
    moved_up = [items[i] for i in moves if moves[i] == "today" and i in items and startable(items[i])]
    forced = moved_up + [i for i in ready if i.get("urgent") and i["id"] not in moves]
    rest = [i for i in ready if i["id"] not in moves and not i.get("urgent")]
    later = [i for i in ready if moves.get(i["id"]) == "later"]
    used, full, above, below = waiting + sum(item_minutes(i) for i in forced), False, [], []
    for item in rest:
        fits = not full and used + item_minutes(item) <= minutes
        full = full or not fits
        used += item_minutes(item) if fits else 0
        (above if fits else below).append(item)
    return [
        {"id": item["id"], "minutes": item_minutes(item), "today": up, "moved": moves.get(item["id"])}
        for items_, up in ((forced, True), (above, True), (below, False), (later, False))
        for item in items_
    ]


def plan_day(items: dict[str, dict], threads: dict, incoming: list[dict], health: dict | None, worktrees: dict) -> dict:
    """What waits on me, and the Today list that fits in the rest of my budget."""
    spaces = spaces_setting()
    now = now_rows(items, threads, incoming, health, worktrees, spaces)
    plan, minutes = today_plan(items), budget()
    waiting = sum(row["minutes"] for row in now)
    rows = today_rows(items, plan, minutes, waiting, spaces)
    return {"now": now, "date": plan["date"], "moves": plan["moves"], "budget": minutes, "waiting": waiting, "rows": rows}


def apply_status(item: dict, status: str) -> None:
    """Set an item's status and the fields that follow from it."""
    if item["status"] == "started" and status == "open":
        item["paused"] = datetime.datetime.now().isoformat(timespec="seconds")
    elif status != "open":
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
    item.pop("rank", None)
    if status == "requested":
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
    for item_id in ids:
        item = items[item_id]
        old = item["status"]
        allowed = {"open", "done"} if old == "started" else SETTABLE_STATUSES - ({"done"} if old == "new" else set())
        retry = status == "requested" and item.get("needs")
        if old == status and not retry or old == "done" or status not in allowed:
            continue
        apply_status(item, status)
        item.pop("adopted", None)
        if status == "requested" and old != "requested":
            item.pop("start_note", None)
            if saved_note:
                item["start_note"] = saved_note
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
        elif url.path.startswith(("/review/", "/api/review/")):
            reviews.get(self, url.path)
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self.allowed() or self.headers.get("Content-Type") != "application/json":
            self.send_json(403, {"error": "forbidden"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path.startswith("/api/review/"):
            reviews.post(self, self.path, body)
            return
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
                        **({"minutes": int(body["minutes"])} if body.get("minutes") else {}),
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
            elif self.path == "/api/today":
                place_today(body["id"], body.get("to"))
                if body.get("to") == "today":
                    plan_changed()
            elif self.path == "/api/budget":
                minutes = int(body["minutes"])
                if not 0 <= minutes <= 24 * 60:
                    raise ValueError("give the budget in minutes of one day")
                write_json(BUDGET, {"minutes": minutes})
                plan_changed()
            elif self.path == "/api/fate":
                if body["pick"] not in FATES:
                    raise ValueError(f"unknown fate {body['pick']}")
                path = item_path(body["id"])
                item = json.loads(path.read_text())
                item.pop("fate", None)
                if body["pick"] == "keep":
                    item["kept"] = datetime.datetime.now().isoformat(timespec="seconds")
                write_json(path, item)
                if body["pick"] == "keep":
                    plan_changed()
                else:
                    set_status([body["id"]], "requested" if body["pick"] == "start" else "dropped")
            elif self.path == "/api/ask/open":
                path = item_path(body["id"])
                item = json.loads(path.read_text())
                if item.get("asks") and not item["asks"].get("opened"):
                    item["asks"]["opened"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
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
                AUTOSTART_LAST.unlink(missing_ok=True)
                log_event({"type": "autostart"})
            elif self.path == "/api/spaces":
                change_spaces(body)
            elif self.path == "/api/update":
                known = {e["slug"] for e in efforts()}
                fields = {k: (v or None) for k, v in body["fields"].items() if k in ("effort", "repo", "urgent")}
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
                    if "blockedBy" in fields and item.get("blockedBy") and not fields["blockedBy"]:
                        item["unblocked"] = now
                    elif fields.get("blockedBy"):
                        item.pop("unblocked", None)
                    item.update(fields)
                    if "urgent" in fields and not fields["urgent"]:
                        item.pop("urgent")
                    write_json(path, item)
                if fields.get("urgent"):
                    plan_changed()
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
