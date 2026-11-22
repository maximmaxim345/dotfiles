#!/usr/bin/env python3
"""Build self-contained HTML review pages from a git diff and a narrative JSON file."""

from __future__ import annotations

import argparse
import codecs
import hashlib
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ASSETS = Path(__file__).resolve().parent / "assets"
REVIEW_PATHS = Path(__file__).resolve().parent / "review-paths.json"
EXPAND_LINES = 100
PROSE_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc"}
TIERS = ["fixup", "small", "normal", "risky"]
TIER_TAGS = {"fixup": "good", "small": "", "normal": "warn", "risky": "bad"}
RISK_TAGS = {"low": "", "medium": "warn", "high": "bad"}
PROOF_TAGS = {"test": ("good", "Test"), "run": ("good", "Run"), "recording": ("good", "Recording"), "none": ("warn", "No proof")}
STATUS_TAGS = {"changed": ("good", "Changed"), "partly": ("warn", "Partly changed"), "declined": ("warn", "Not changed")}
DIFF_ARGS = ["--no-color", "--no-ext-diff", "--no-textconv", "--unified=3", "--src-prefix=a/", "--dst-prefix=b/"]
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$")
TOP_BAR_CONTROLS = (
    '<div class="ctl"><span class="seg" role="group" aria-label="Diff layout">'
    '<button data-layout="auto">Auto</button><button data-layout="split">Side by side</button>'
    '<button data-layout="unified">Stacked</button></span>'
    '<label class="chk"><input type="checkbox" id="wrap"> Wrap lines</label></div>'
)
BOTTOM_BAR = (
    '<div class="bar" id="bar"><div class="tray" id="tray" hidden></div><div class="bar-in">'
    '<span class="status" id="status"></span><button class="btn" id="show">Show</button>'
    '<button class="btn primary" id="copy">Copy for chat</button></div></div>'
)
UNCOMMITTED = "uncommitted"
BLAME_RE = re.compile(r"^([0-9a-f]{40}) \d+ (\d+)(?: \d+)?$")
LINE_REF_RE = re.compile(r"(?<![\w/.~-])([\w.~-]+(?:/[\w.~-]+)*):(\d+)(?:-(\d+))?(?![\w-])")
DIFF_HEADERS = (
    "index ",
    "--- ",
    "+++ ",
    "rename from ",
    "rename to ",
    "copy from ",
    "copy to ",
    "similarity index ",
    "dissimilarity index ",
    "new file mode ",
    "deleted file mode ",
    "old mode ",
    "new mode ",
    "Binary files ",
)
CR_MARK = '<span class="cr" title="carriage return">\u240d</span>'
SVG_NS = "{http://www.w3.org/2000/svg}"
SVG_ELEMENTS = set(
    (
        "svg g defs title desc rect circle ellipse line polyline polygon path text tspan marker linearGradient"
        " radialGradient stop clipPath"
    ).split()
)
SVG_ATTRIBUTES = set(
    (
        "viewBox width height x y x1 y1 x2 y2 cx cy r rx ry d points dx dy fill fill-opacity fill-rule stroke"
        " stroke-width stroke-opacity stroke-dasharray stroke-linecap stroke-linejoin opacity transform class id"
        " text-anchor dominant-baseline font-size font-weight font-family font-style marker-start marker-mid marker-end"
        " markerWidth markerHeight markerUnits refX refY orient preserveAspectRatio offset stop-color stop-opacity"
        " gradientUnits gradientTransform clip-path role aria-label aria-hidden"
    ).split()
)
EXTERNAL_URL_RE = re.compile(r"url\(\s*['\"]?(?!#)", re.I)
WEB_URL_RE = re.compile(r"(https?://[^\s<>\"'`]*[^\s<>\"'`.,:;)])")

ReadLines = Callable[[str], Optional[List[str]]]


class KitError(Exception):
    pass


@dataclass
class Hunk:
    path: str
    old_path: str
    old_start: int = 0
    old_count: int = 0
    new_start: int = 0
    new_count: int = 0
    header: str = ""
    lines: List[List[str]] = field(default_factory=list)
    note: str = ""
    id: str = ""
    above: Optional[Dict[str, Any]] = None
    below: Optional[Dict[str, Any]] = None
    commits: List[str] = field(default_factory=list)
    skim: str = ""
    look: str = ""
    no_newline: List[int] = field(default_factory=list)

    @property
    def first_new(self) -> int:
        return self.new_start if self.new_count else self.new_start + 1

    @property
    def last_new(self) -> int:
        return self.first_new + self.new_count - 1

    @property
    def added(self) -> int:
        return sum(1 for kind, _ in self.lines if kind == "+")

    @property
    def removed(self) -> int:
        return sum(1 for kind, _ in self.lines if kind == "-")

    @property
    def prose(self) -> bool:
        return Path(self.path).suffix.lower() in PROSE_SUFFIXES

    def numbered(self) -> List[Tuple[str, int]]:
        old, new, out = self.old_start, self.new_start, []
        for kind, _ in self.lines:
            if kind == "-":
                out.append(("-", old))
                old += 1
            elif kind == "+":
                out.append(("+", new))
                new += 1
            else:
                old += 1
                new += 1
        return out

    def changed(self, kind: str) -> str:
        numbers = [n for k, n in self.numbered() if k == kind]
        if not numbers:
            return ""
        return f"{numbers[0]}-{numbers[-1]}" if numbers[-1] > numbers[0] else str(numbers[0])

    @property
    def shown(self) -> Tuple[int, int]:
        first = self.above["new"] if self.above else self.first_new
        last = self.below["new"] + len(self.below["lines"]) - 1 if self.below else self.last_new
        return first, last

    @property
    def range_label(self) -> str:
        if not self.lines:
            return ""
        if self.new_count:
            return f"{self.first_new}-{self.last_new}" if self.new_count > 1 else str(self.first_new)
        return f"removed at old {self.old_start}-{self.old_start + self.old_count - 1}"

    @property
    def where(self) -> str:
        return f"{self.path}:{self.range_label}" if self.lines else self.path

    def to_page(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "oldStart": self.old_start,
            "oldCount": self.old_count,
            "newStart": self.new_start,
            "newCount": self.new_count,
            "header": "" if self.prose else self.header,
            "lines": self.lines,
            "note": self.note,
            "prose": self.prose,
            "above": self.above,
            "below": self.below,
            "commits": [c[:7] if c != UNCOMMITTED else c for c in self.commits],
            "skim": self.skim,
            "noNewline": self.no_newline,
        }


@dataclass
class Change:
    hunks: List[Hunk]
    start: str
    head: Optional[str]
    base: str
    commits: List[Tuple[str, str]]
    read: ReadLines
    reviewed: str = ""
    notice: str = ""
    branch: str = ""
    remotes: List[str] = field(default_factory=list)
    diff_hash: str = ""


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # Decode by hand, since text mode turns a carriage return into a line break.
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotePath=false", *args], capture_output=True)
    return subprocess.CompletedProcess(
        result.args, result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")
    )


def git(repo: Path, *args: str) -> str:
    result = run_git(repo, *args)
    if result.returncode != 0:
        raise KitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def rev(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()


def unquote(path: str) -> str:
    if len(path) > 1 and path.startswith('"') and path.endswith('"'):
        return codecs.decode(path[1:-1].encode("utf-8"), "unicode_escape").encode("latin-1").decode("utf-8", "replace")
    return path


def strip_prefix(path: str) -> str:
    path = unquote(path)
    return path[2:] if path[:2] in ("a/", "b/") else path


def paths_from_diff_line(line: str) -> Tuple[str, str]:
    rest = line[len("diff --git ") :]
    quoted = re.fullmatch(r'("(?:[^"\\]|\\.)*"|\S+) ("(?:[^"\\]|\\.)*"|\S+)', rest)
    if quoted:
        return strip_prefix(quoted[1]), strip_prefix(quoted[2])
    half = (len(rest) - 1) // 2
    return strip_prefix(rest[:half]), strip_prefix(rest[half + 1 :])


def parse_file(lines: List[str]) -> List[Hunk]:
    old_path, new_path = paths_from_diff_line(lines[0])
    notes: List[str] = []
    modes: Dict[str, str] = {}
    i = 1
    while i < len(lines) and not lines[i].startswith("@@"):
        line = lines[i]
        if not line.startswith(DIFF_HEADERS):
            raise KitError(f"Cannot read this header line of the diff of {new_path}: {line[:80]!r}")
        name = line[4:].rstrip("\t")
        if line.startswith("--- ") and name != "/dev/null":
            old_path = strip_prefix(name)
        elif line.startswith("+++ ") and name != "/dev/null":
            new_path = strip_prefix(name)
        elif line.startswith("rename from "):
            old_path = unquote(line[len("rename from ") :])
        elif line.startswith("rename to "):
            new_path = unquote(line[len("rename to ") :])
        elif line.startswith("new file mode"):
            notes.append("New file.")
        elif line.startswith("deleted file mode"):
            notes.append("Deleted file.")
        elif line.startswith(("old mode ", "new mode ")):
            modes[line.split()[0]] = line.split()[-1]
        elif line.startswith("Binary files"):
            notes.append("Binary file, its contents are not shown.")
        i += 1
    if old_path != new_path:
        notes.append(f"Renamed from {old_path}.")
    if modes:
        notes.append(f"File mode changed from {modes.get('old', '?')} to {modes.get('new', '?')}.")
    hunks: List[Hunk] = []
    for line in lines[i:]:
        match = HUNK_RE.match(line)
        if match:
            hunks.append(
                Hunk(
                    path=new_path,
                    old_path=old_path,
                    old_start=int(match[1]),
                    old_count=int(match[2] if match[2] is not None else 1),
                    new_start=int(match[3]),
                    new_count=int(match[4] if match[4] is not None else 1),
                    header=match[5].strip(),
                )
            )
        elif hunks and line[:1] in (" ", "+", "-"):
            hunks[-1].lines.append([line[0], line[1:]])
        elif hunks and hunks[-1].lines and line.startswith("\\ "):
            hunks[-1].no_newline.append(len(hunks[-1].lines) - 1)
        else:
            raise KitError(f"Cannot read this line of the diff of {new_path}: {line[:80]!r}")
    for hunk in hunks:
        old = sum(1 for kind, _ in hunk.lines if kind != "+")
        new = sum(1 for kind, _ in hunk.lines if kind != "-")
        if (old, new) != (hunk.old_count, hunk.new_count):
            raise KitError(f"A hunk of {new_path} at old line {hunk.old_start} does not have the lines its header counts")
    if not hunks:
        hunks.append(Hunk(path=new_path, old_path=old_path, note=" ".join(notes) or "Empty file."))
    else:
        hunks[0].note = " ".join(notes)
    return hunks


def parse_diff(text: str) -> List[Hunk]:
    hunks: List[Hunk] = []
    chunks = re.split(r"^(?=diff --git )", text, flags=re.M)
    if chunks[0]:
        raise KitError(f"The diff starts with a line that is not a file header: {chunks[0][:80]!r}")
    for chunk in chunks[1:]:
        lines = chunk.split("\n")
        if lines[-1] == "":
            lines.pop()
        hunks.extend(parse_file(lines))
    seen: Dict[str, int] = {}
    for hunk in hunks:
        marked = [kind + text + ("\n\\" if index in hunk.no_newline else "") for index, (kind, text) in enumerate(hunk.lines)]
        body = "\n".join(line for line in marked if line[0] != " ") or hunk.note
        digest = hashlib.sha1(f"{hunk.path}\0{body}".encode("utf-8")).hexdigest()[:8]
        seen[digest] = seen.get(digest, 0) + 1
        hunk.id = f"h{digest}" if seen[digest] == 1 else f"h{digest}-{seen[digest]}"
    return hunks


def diff_text(repo: Path, start: str, head: Optional[str]) -> str:
    text = git(repo, "diff", *DIFF_ARGS, "-M", start, *([head] if head else []))
    if head is None:
        for path in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
            if path:
                result = run_git(repo, "diff", "--no-index", *DIFF_ARGS, "--", "/dev/null", path)
                if result.returncode not in (0, 1):
                    raise KitError(f"git diff --no-index {path} failed: {result.stderr.strip()}")
                text += result.stdout
    return text


def file_reader(repo: Path, head: Optional[str]) -> ReadLines:
    cache: Dict[str, Optional[List[str]]] = {}

    def read(path: str) -> Optional[List[str]]:
        if path not in cache:
            if head is None:
                try:
                    data: Optional[bytes] = (repo / path).read_bytes()
                except OSError:
                    data = None
            else:
                result = subprocess.run(["git", "-C", str(repo), "show", f"{head}:{path}"], capture_output=True)
                data = result.stdout if result.returncode == 0 else None
            if data is None or b"\0" in data[:8000]:
                cache[path] = None
            else:
                text = data.decode("utf-8", "replace")
                cache[path] = text[:-1].split("\n") if text.endswith("\n") else text.split("\n")
        return cache[path]

    return read


def add_windows(hunks: List[Hunk], read: ReadLines) -> None:
    by_path: Dict[str, List[Hunk]] = {}
    for hunk in hunks:
        if hunk.lines:
            by_path.setdefault(hunk.path, []).append(hunk)
    for path, file_hunks in by_path.items():
        content = read(path)
        if content is None:
            continue
        previous_last = 0
        for index, hunk in enumerate(file_hunks):
            next_first = file_hunks[index + 1].first_new if index + 1 < len(file_hunks) else len(content) + 1
            old_first = hunk.old_start if hunk.old_count else hunk.old_start + 1
            old_last = old_first + hunk.old_count - 1
            gap = hunk.first_new - 1 - previous_last
            if gap > 0:
                take = min(gap, EXPAND_LINES)
                start = hunk.first_new - take
                hunk.above = {
                    "new": start,
                    "old": start - (hunk.first_new - old_first),
                    "lines": content[start - 1 : hunk.first_new - 1],
                    "more": gap - take,
                }
            gap = next_first - 1 - hunk.last_new
            if gap > 0:
                take = min(gap, EXPAND_LINES)
                start = hunk.last_new + 1
                hunk.below = {
                    "new": start,
                    "old": start - (hunk.last_new - old_last),
                    "lines": content[start - 1 : start - 1 + take],
                    "more": gap - take,
                }
            previous_last = hunk.last_new


def branch_of(repo: Path, ref: str) -> str:
    result = run_git(repo, "rev-parse", "--symbolic-full-name", ref)
    name = result.stdout.strip() if result.returncode == 0 else ""
    for prefix in ("refs/heads/", "refs/remotes/"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return ""


def remote_names(repo: Path) -> List[str]:
    names = []
    for remote in ("upstream", "origin"):
        result = run_git(repo, "remote", "get-url", remote)
        match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$", result.stdout.strip()) if result.returncode == 0 else None
        if match:
            names.append(match[1])
    return names


def glob_regex(pattern: str) -> "re.Pattern[str]":
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        else:
            out, i = out + {"*": "[^/]*", "?": "[^/]"}.get(pattern[i], re.escape(pattern[i])), i + 1
    return re.compile(out)


def mark_look_paths(hunks: List[Hunk], repos: List[str]) -> None:
    try:
        data = json.loads(REVIEW_PATHS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise KitError(f"Cannot read {REVIEW_PATHS}: {error}") from error
    wanted = {repo.lower() for repo in repos}
    rules = [(glob_regex(p), why) for repo, paths in data.items() if repo.lower() in wanted for p, why in paths.items()]
    for hunk in hunks:
        hunk.look = next((why for rule, why in rules if rule.fullmatch(hunk.path) or rule.fullmatch(hunk.old_path)), "")


def blame(repo: Path, path: str, ranges: List[str], *revs: str) -> Optional[Dict[int, str]]:
    args = ["blame", "--porcelain", *revs]
    for spec in ranges:
        first, last = parse_lines(spec)
        args += ["-L", f"{first},{last}"]
    result = run_git(repo, *args, "--", path)
    if result.returncode != 0:
        return None
    return {int(m[2]): m[1] for m in map(BLAME_RE.match, result.stdout.split("\n")) if m}


def attribute(repo: Path, change: Change, log_from: str) -> None:
    order = [sha for sha, _ in change.commits]
    found: Dict[str, set] = {h.id: set() for h in change.hunks}
    added: Dict[str, List[Hunk]] = {}
    removed: Dict[str, List[Hunk]] = {}
    for hunk in change.hunks:
        if hunk.added:
            added.setdefault(hunk.path, []).append(hunk)
        if hunk.removed and change.start == log_from:
            removed.setdefault(hunk.old_path, []).append(hunk)
    span = f"{log_from}..{change.head}" if change.head else f"^{log_from}"
    for path, hunks in added.items():
        lines = blame(repo, path, [h.changed("+") for h in hunks], span)
        for hunk in hunks:
            if lines is None:
                found[hunk.id].update([UNCOMMITTED] if change.head is None else [])
                continue
            for kind, number in hunk.numbered():
                sha = lines.get(number, "") if kind == "+" else ""
                if sha and not sha.strip("0"):
                    found[hunk.id].add(UNCOMMITTED)
                elif sha in order:
                    found[hunk.id].add(sha)
    for path, hunks in removed.items():
        lines = blame(repo, path, [h.changed("-") for h in hunks], "--reverse", f"{log_from}..{change.head or 'HEAD'}")
        for hunk in hunks:
            for kind, number in hunk.numbered():
                sha = (lines or {}).get(number, "") if kind == "-" else ""
                if sha == log_from and order:
                    found[hunk.id].add(order[0])
                elif sha in order[:-1]:
                    found[hunk.id].add(order[order.index(sha) + 1])
                elif sha and sha == (order[-1] if order else log_from) and change.head is None:
                    found[hunk.id].add(UNCOMMITTED)
    rank = {sha: index for index, sha in enumerate(order + [UNCOMMITTED])}
    for hunk in change.hunks:
        hunk.commits = sorted(found[hunk.id], key=rank.__getitem__)


def replay_start(repo: Path, base_ref: str, base: str, since: str) -> Tuple[str, str]:
    old_head = rev(repo, since)
    old_base = git(repo, "merge-base", base_ref, old_head).strip()
    if old_base == base:
        return old_head, ""
    result = run_git(repo, "merge-tree", "--write-tree", f"--merge-base={old_base}", base, old_head)
    if result.returncode == 0:
        return result.stdout.split("\n")[0].strip(), (
            f"The branch moved to a new base ({old_base[:7]} to {base[:7]}). The previously reviewed head was replayed "
            "onto the new base before comparing, so changes that came with the new base are left out."
        )
    return old_head, (
        f"The branch moved to a new base ({old_base[:7]} to {base[:7]}) and the previously reviewed head does not replay "
        "onto it cleanly. This page compares the two heads directly, so changes that came with the new base show up too."
    )


def collect(
    repo: Path, base: Optional[str], head_ref: Optional[str], span: Optional[str], uncommitted: bool, since: Optional[str]
) -> Change:
    if span:
        if "..." in span or ".." not in span:
            raise KitError("--range takes the form A..B")
        base_ref, head_ref = span.split("..", 1)
        head = rev(repo, head_ref or "HEAD")
        base_commit = rev(repo, base_ref)
    elif base:
        base_ref = base
        head = rev(repo, head_ref or "HEAD")
        base_commit = git(repo, "merge-base", base, head).strip()
    else:
        raise KitError("Pass --base REF or --range A..B")
    start, notice = (base_commit, "") if since is None else replay_start(repo, base_ref, base_commit, since)
    log_from = base_commit
    reviewed = rev(repo, since) if since is not None else ""
    if reviewed and run_git(repo, "merge-base", "--is-ancestor", reviewed, head).returncode == 0:
        log_from = reviewed
    log = git(repo, "log", "--reverse", "--format=%H%x09%s", f"{log_from}..{head}").split("\n")
    commits = [(line[:40], line[41:]) for line in log if line]
    tree_head: Optional[str] = head
    if uncommitted:
        if head != rev(repo, "HEAD"):
            raise KitError("--uncommitted needs the head to be HEAD")
        tree_head = None
    text = diff_text(repo, start, tree_head)
    hunks = parse_diff(text)
    read = file_reader(repo, tree_head)
    add_windows(hunks, read)
    change = Change(
        hunks=hunks,
        start=start,
        head=tree_head,
        base=base_commit,
        commits=commits,
        read=read,
        reviewed=reviewed,
        notice=notice,
        branch=branch_of(repo, head_ref or "HEAD"),
        remotes=remote_names(repo),
        diff_hash="" if tree_head else hashlib.sha1(text.encode("utf-8")).hexdigest(),
    )
    attribute(repo, change, log_from)
    mark_look_paths(hunks, change.remotes)
    return change


def plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def esc(text: Any) -> str:
    return html.escape(str(text))


def esc_line(text: str) -> str:
    return esc(text).replace("\r", CR_MARK)


class Linker:
    def __init__(self, hunks: List[Hunk]) -> None:
        self.hunks = [h for h in hunks if h.lines]

    def anchor(self, hunk: Hunk, first: int, last: int, label: str, cls: str = "lref") -> str:
        return f'<a class="{cls}" href="#hunk-{hunk.id}" data-lines="{first}-{last}">{label}</a>'

    def link(self, match: "re.Match[str]", label: str) -> Optional[str]:
        first = int(match[2])
        paths = {h.path for h in self.hunks if h.path == match[1] or h.path.endswith("/" + match[1])}
        if len(paths) != 1:
            return None
        held = [h for h in self.hunks if h.path in paths and h.shown[0] <= first <= h.shown[1]]
        hunk = next((h for h in held if h.first_new <= first <= h.last_new), held[0] if held else None)
        if not hunk:
            return None
        last = min(max(first, int(match[3] or first)), hunk.shown[1])
        return self.anchor(hunk, first, last, label)

    def text(self, raw: str) -> str:
        out, at = "", 0
        for match in LINE_REF_RE.finditer(raw):
            link = self.link(match, esc(match[0]))
            if link:
                out += esc(raw[at : match.start()]) + link
                at = match.end()
        return out + esc(raw[at:])

    def code(self, raw: str) -> str:
        match = LINE_REF_RE.fullmatch(raw)
        code = f"<code>{esc(raw)}</code>"
        return (self.link(match, code) if match else None) or code


def inline(text: Any, linker: Optional[Linker] = None, links: bool = True) -> str:
    out = ""
    for part in re.split(r"(`[^`\n]+`)", str(text)):
        if part.startswith("`") and part.endswith("`") and len(part) > 2:
            out += linker.code(part[1:-1]) if linker else f"<code>{esc(part[1:-1])}</code>"
            continue
        for index, piece in enumerate(WEB_URL_RE.split(part) if links else [part]):
            if index % 2:
                out += f'<a href="{esc(piece)}" target="_blank" rel="noreferrer">{esc(piece)}</a>'
            else:
                out += linker.text(piece) if linker else esc(piece)
    return out


def prose(text: Any, linker: Optional[Linker] = None) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", str(text or "")) if p.strip()]
    return "".join("<p>" + inline(p, linker).replace("\n", "<br>") + "</p>" for p in paragraphs)


def parse_lines(spec: Any) -> Tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*", str(spec))
    if not match:
        raise KitError(f"Line range must look like 10 or 10-20, got {spec!r}")
    first, last = int(match[1]), int(match[2] or match[1])
    return min(first, last), max(first, last)


def resolve(ref: Any, hunks: List[Hunk]) -> List[Hunk]:
    if isinstance(ref, str):
        ref = {"hunk": ref}
    if not isinstance(ref, dict):
        raise KitError(f"A hunk reference is an id or an object, got {ref!r}")
    if "hunk" in ref:
        found = [h for h in hunks if h.id == ref["hunk"]]
    elif "file" in ref:
        found = [h for h in hunks if ref["file"] in (h.path, h.old_path)]
        if "lines" in ref:
            first, last = parse_lines(ref["lines"])
            found = [h for h in found if not h.lines or (h.first_new <= last and first <= max(h.last_new, h.first_new))]
    else:
        raise KitError(f"A hunk reference needs `hunk` or `file`: {json.dumps(ref)}")
    if not found:
        raise KitError(f"No hunk matches {json.dumps(ref)}. Run with --list-hunks to see the hunks.")
    return found


def context_panel(ref: Dict[str, Any], read: ReadLines) -> str:
    if "file" not in ref or "lines" not in ref:
        raise KitError(f"A context reference needs `file` and `lines`: {json.dumps(ref)}")
    content = read(ref["file"])
    if content is None:
        raise KitError(f"Cannot read {ref['file']} for a context panel")
    first, last = parse_lines(ref["lines"])
    if first > len(content):
        raise KitError(f"{ref['file']} has {len(content)} lines, the context starts at {first}")
    last = min(last, len(content))
    rows = "".join(
        f'<tr><td class="ln">{n}</td><td class="c">{esc_line(content[n - 1])}</td></tr>' for n in range(first, last + 1)
    )
    note = f' <span class="muted">{inline(ref["note"])}</span>' if ref.get("note") else ""
    return (
        f'<details class="ctxp" open><summary><span class="muted">Unchanged</span> <code>{esc(ref["file"])}:{first}-{last}</code>'
        f'{note}</summary><div class="dscroll"><table class="d">{rows}</table></div></details>'
    )


class Layout:
    def __init__(self, change: Change) -> None:
        self.change = change
        self.linker = Linker(change.hunks)
        self.placed: Dict[str, str] = {}
        self.unplaced = 0

    def entries(self, items: List[Any], where: str, skim: str = "") -> str:
        out = ""
        for item in items:
            meta = item if isinstance(item, dict) else {}
            found = resolve(item, self.change.hunks)
            if "file" in meta and "lines" not in meta:
                found = [h for h in found if h.id not in self.placed] or found
            for index, hunk in enumerate(found):
                out += self.entry(hunk, meta if index == 0 else {}, where, skim)
        return out

    def entry(self, hunk: Hunk, meta: Dict[str, Any], where: str, skim: str = "") -> str:
        if hunk.id in self.placed:
            note = f" {inline(meta['note'], self.linker)}" if meta.get("note") else ""
            return (
                f'<div class="alias">Shown under {esc(self.placed[hunk.id])}: '
                f'<a href="#hunk-{hunk.id}"><code>{esc(hunk.where)}</code></a>.{note}</div>'
            )
        self.placed[hunk.id] = where
        hunk.skim = skim
        why = prose(meta.get("note", ""), self.linker)
        look = meta.get("look")
        tags = ""
        if look:
            label = "Look closely" if look is True else f"Look closely: {look}"
            tags += f'<span class="tag accent">{inline(label)}</span>'
        if hunk.look:
            tags += f'<span class="tag accent">Look closely: {esc(hunk.look)}</span>'
        if tags:
            why += f"<p>{tags}</p>"
        panels = "".join(context_panel(ref, self.change.read) for ref in meta.get("context", []))
        return (
            f'<article class="hunk" data-hunk="{hunk.id}" id="hunk-{hunk.id}">'
            + (f'<div class="why">{why}</div>' if why else "")
            + panels
            + '<div class="hbody"></div></article>'
        )

    def group(self, group: Dict[str, Any], number: int) -> str:
        hunks = group.get("hunks", [])
        if group.get("unimportant"):
            if not group.get("reason"):
                raise KitError(f"Unimportant group {number} needs a `reason`")
            if group.get("note"):
                raise KitError(f"Unimportant group {number} shows no `note`, put it on one of its hunks")
            count = len({h.id for item in hunks for h in resolve(item, self.change.hunks)})
            files = len({h.path for item in hunks for h in resolve(item, self.change.hunks)})
            label = group["reason"]
            body = self.entries(hunks, f'"{label}"', label)
            looked = len({h.id for item in hunks for h in resolve(item, self.change.hunks) if h.look})
            flag = f'<span class="tag accent">{looked} to look closely</span>' if looked else ""
            return (
                f'<details class="group skim"><summary><b>{inline(label)}</b>'
                f'<span class="count">{plural(count, "hunk")} in {plural(files, "file")}</span>{flag}'
                f'<span class="go">Show</span></summary>{body}</details>'
            )
        title = group.get("title") or f"Group {number}"
        body = self.entries(hunks, f'"{number}. {title}"')
        note = f'<div class="gnote">{prose(group["note"], self.linker)}</div>' if group.get("note") else ""
        return f'<section class="group"><h3>{number}. {inline(title)}</h3>{note}{body}</section>'

    def groups(self, groups: List[Dict[str, Any]]) -> str:
        return "".join(self.group(group, number) for number, group in enumerate(groups, 1))

    def unmentioned(self) -> str:
        rest = [h for h in self.change.hunks if h.id not in self.placed]
        self.unplaced = len(rest)
        if not rest:
            return ""
        body = "".join(self.entry(h, {}, '"Not mentioned by the author"') for h in rest)
        return (
            f'<section class="group unmentioned"><h3>Not mentioned by the author <span class="count">{len(rest)}</span></h3>'
            f'<p class="gnote">The narrative does not place these hunks. They are shown in file order.</p>{body}</section>'
        )


def choices(options: List[Dict[str, Any]], pick: Any, where: str) -> Tuple[str, str]:
    ids = [opt.get("id") or chr(ord("A") + i) for i, opt in enumerate(options)]
    pick = pick or (ids[0] if ids else "")
    if ids and pick not in ids:
        raise KitError(f"{where}: pick {pick!r} is not one of {ids}")
    buttons = ""
    for i, opt in enumerate(options):
        oid = ids[i]
        sug = "<span class=sug>Pick</span>" if oid == pick else ""
        buttons += (
            f'<button class="opt{" suggest" if oid == pick else ""}" data-opt="{esc(oid)}"><span class="ol">{esc(oid)}</span>'
            f'<span>{inline(opt.get("text", ""), links=False)}</span>{sug}</button>'
        )
    return str(pick), buttons


def ref_links(ref: Any, change: Change, linker: Linker) -> str:
    out = ""
    for hunk in resolve(ref, change.hunks):
        if isinstance(ref, dict) and "lines" in ref and hunk.lines:
            first, last = parse_lines(ref["lines"])
            first, last = max(first, hunk.first_new), min(last, max(hunk.last_new, hunk.first_new))
            label = f"{hunk.path}:{first}-{last}" if last > first else f"{hunk.path}:{first}"
            out += linker.anchor(hunk, first, last, esc(label), "golink")
        else:
            out += f'<a class="golink" href="#hunk-{hunk.id}">{esc(hunk.where)}</a>'
    return out


def decide_cards(cards: List[Dict[str, Any]], change: Change, linker: Linker, order: str) -> str:
    if not cards:
        return ""
    out = ""
    for number, card in enumerate(cards, 1):
        pick, buttons = choices(card.get("options", []), card.get("pick"), f"Decide card {number}")
        risk = str(card.get("risk_level", "")).lower()
        tags = f'<span class="tag {RISK_TAGS.get(risk, "")}">{esc(risk.capitalize())} risk</span>' if risk else ""
        tags += f'<span class="tag">{inline(card["undo"])}</span>' if card.get("undo") else ""
        links = "".join(ref_links(ref, change, linker) for ref in card.get("refs", []))
        body = ""
        for key, label in (("risk", "Risk."), ("evidence", "Evidence.")):
            if card.get(key):
                body += f'<p><span class="lbl">{label}</span> {inline(card[key], linker)}</p>'
        if links:
            body += f"<p>{links}</p>"
        if card.get("why"):
            body += f'<p><span class="lbl">Pick {esc(pick)}.</span> {inline(card["why"], linker)}</p>'
        panels = "".join(context_panel(ref, change.read) for ref in card.get("context", []))
        out += (
            f'<article class="card call" data-call="{number}" data-pick="{esc(pick)}">'
            f'<div class="call-top"><span class="num">Decide {number}</span>{tags}</div>'
            f'<h3>{inline(card.get("title", ""), linker)}</h3><div class="prose">{body}</div>{panels}'
            f'<div class="opts">{buttons}</div></article>'
        )
    count = f"{len(cards)}, {esc(order)}" if order else str(len(cards))
    return (
        f'<section id="decide"><h2>Decide <span class="count">{count}</span></h2>'
        f'<p class="sub">Each card has a pick. Pick another option to change it, it goes out with Copy for chat.</p>'
        f'<div class="calls">{out}</div></section>'
    )


def behavior_table(behavior: Any, linker: Linker) -> str:
    if not behavior:
        return ""
    rows = behavior.get("rows", []) if isinstance(behavior, dict) else behavior
    body = "".join(
        f'<tr><td>{inline(r.get("case", ""), linker)}</td><td data-l="Before">{inline(r.get("before", ""), linker)}</td>'
        f'<td data-l="After">{inline(r.get("after", ""), linker)}</td></tr>'
        for r in rows
    )
    unchanged = behavior.get("unchanged") if isinstance(behavior, dict) else None
    tail = f'<div class="small muted" style="margin-top:8px">{prose(unchanged, linker)}</div>' if unchanged else ""
    return (
        '<section id="behavior"><h2>Behavior before and after</h2>'
        f'<table class="beh card"><thead><tr><th>Case</th><th>Before</th><th>After</th></tr></thead><tbody>{body}</tbody></table>'
        f"{tail}</section>"
    )


def claims_section(narrative: Dict[str, Any], change: Change, linker: Linker) -> str:
    claims = narrative.get("claims") or []
    rows, unproven = "", 0
    for number, claim in enumerate(claims, 1):
        proof = claim.get("proof", "none")
        if proof not in PROOF_TAGS:
            raise KitError(f"Claim {number}: `proof` must be one of {list(PROOF_TAGS)}, got {proof!r}")
        unproven += proof == "none"
        tag, label = PROOF_TAGS[proof]
        body = f'<span class="tag {tag}">{label}</span>'
        body += f"<code>{esc(claim['name'])}</code>" if claim.get("name") else ""
        if proof == "test":
            without = claim.get("fails_without")
            body += {
                True: ' <span class="res good">fails without the change</span>',
                False: ' <span class="res warn">passes without the change</span>',
            }.get(without, ' <span class="res">not run without the change</span>')
        body += prose(claim.get("detail", ""), linker)
        links = "".join(ref_links(ref, change, linker) for ref in claim.get("refs", []))
        body += f"<p>{links}</p>" if links else ""
        rows += (
            f'<div class="claim{" unchecked" if proof == "none" else ""}"><div class="ct">{number}. '
            f'{inline(claim.get("claim", ""), linker)}</div><div class="pf">{body}</div></div>'
        )
    if not rows:
        return ""
    count = plural(len(claims), "claim") + (f", {unproven} without proof" if unproven else "")
    note = f'<p class="sub">{inline(narrative["claims_note"], linker)}</p>' if narrative.get("claims_note") else ""
    return (
        f'<section id="claims"><h2>Claims and proof <span class="count">{count}</span></h2>{note}'
        f'<div class="claims">{rows}</div></section>'
    )


def reviewers_section(narrative: Dict[str, Any], linker: Linker) -> str:
    rows = ""
    for reviewer in narrative.get("reviewers") or []:
        fixed = reviewer.get("fixed") or []
        kept = reviewer.get("kept") or []
        counts = []
        if "fixed" in reviewer:
            counts.append(f"Fixed {fixed if isinstance(fixed, int) else len(fixed)}.")
        if "kept" in reviewer:
            counts.append(f"Kept {len(kept)}.")
        if "skipped" in reviewer:
            counts.append(f"Skipped {esc(reviewer['skipped'])} theoretical.")
        line = f"<p>{' '.join(counts)}</p>" if counts else ""
        items = "" if isinstance(fixed, int) else "".join(f"<li>Fixed: {inline(f, linker)}</li>" for f in fixed)
        for item in kept:
            finding, why = (item.get("finding", ""), item.get("why", "")) if isinstance(item, dict) else (item, "")
            items += f"<li>Kept: {inline(finding, linker)}" + (f" Why: {inline(why, linker)}" if why else "") + "</li>"
        note = prose(reviewer.get("note", ""), linker)
        rows += (
            f'<div class="rev-row"><b>{inline(reviewer.get("name", ""))}</b><div>{line}'
            f'{f"<ul>{items}</ul>" if items else ""}{note}</div></div>'
        )
    intro = f'<p class="sub">{inline(narrative["reviewers_note"], linker)}</p>' if narrative.get("reviewers_note") else ""
    if not rows and not intro:
        return ""
    card = f'<div class="card rev">{rows}</div>' if rows else ""
    return f'<section id="reviewers"><h2>What the reviewers found</h2>{intro}{card}</section>'


def is_test_path(path: str) -> bool:
    parts = path.lower().split("/")
    return any(p in ("test", "tests", "__tests__", "spec", "specs") for p in parts[:-1]) or bool(
        re.fullmatch(r"test_.*|.*_test\.[^.]+|.*\.(test|spec)\.[^.]+|conftest\.py", parts[-1])
    )


def pick_tier(narrative: Dict[str, Any], hunks: List[Hunk], round_two: bool) -> Tuple[str, str]:
    changed = sum(h.added + h.removed for h in hunks if not is_test_path(h.path))
    if changed > 400:
        floor = "risky"
    elif changed >= 50:
        floor = "normal"
    elif round_two and changed <= 15:
        floor = "fixup"
    else:
        floor = "small"
    wanted = narrative.get("tier")
    if wanted is not None and wanted not in TIERS:
        raise KitError(f"`tier` must be one of {TIERS}, got {wanted!r}")
    line = f"{changed} changed lines outside tests make {floor} the lowest tier."
    looked = sum(1 for h in hunks if h.look)
    if looked and TIERS.index(floor) < TIERS.index("normal"):
        floor = "normal"
        line += f" {plural(looked, 'hunk')} in paths marked for a close look make it at least normal."
    if wanted and TIERS.index(wanted) < TIERS.index(floor):
        line += f" The narrative asked for {wanted}, which is lower, so the page keeps {floor}."
    tier = max(floor, wanted or floor, key=TIERS.index)
    return tier, line


def page(title: str, body: str, css: List[str], js: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> str:
    styles = "\n".join((ASSETS / name).read_text(encoding="utf-8") for name in css)
    scripts = ""
    if js:
        payload = json.dumps(data or {}, ensure_ascii=False).replace("<", "\\u003c")
        code = (ASSETS / js).read_text(encoding="utf-8")
        scripts = f'<script id="kit-data" type="application/json">{payload}</script>\n<script>\n{code}</script>\n'
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<meta name="color-scheme" content="light dark">\n<title>{esc(title)}</title>\n<style>\n{styles}\n</style>\n</head>\n'
        f"<body>\n{body}\n{scripts}</body>\n</html>\n"
    )


def header(narrative: Dict[str, Any], change: Change, tier: str, tier_line: str, linker: Linker) -> str:
    round_two = narrative.get("feedback") is not None
    repo = narrative.get("repo") or (change.remotes[0] if change.remotes else "")
    branch = narrative.get("branch") or change.branch
    head_label = change.head[:7] if change.head else "uncommitted changes"
    added = sum(h.added for h in change.hunks)
    removed = sum(h.removed for h in change.hunks)
    files = len({h.path for h in change.hunks})
    meta = [f"<span><code>{esc(repo)}</code></span>"] if repo else []
    if branch:
        meta.append(f"<span>branch <code>{esc(branch)}</code></span>")
    if round_two:
        meta.append(f"<span>reviewed <code>{change.reviewed[:7]}</code>, now <code>{esc(head_label)}</code></span>")
    else:
        meta.append(f"<span>base <code>{change.base[:7]}</code>, head <code>{esc(head_label)}</code></span>")
    meta.append(f"<span>{plural(len(change.commits), 'commit')}, +{added} -{removed} in {plural(files, 'file')}</span>")
    meta += [f"<span>{inline(item)}</span>" for item in narrative.get("meta", [])]

    tiles = [
        '<div class="fact"><div class="k">Tier</div>'
        f'<div class="v"><span class="tag {TIER_TAGS[tier]}">{tier.capitalize()}</span> '
        f'{inline(narrative.get("tier_reason", ""), linker)}<div class="small muted">{esc(tier_line)}</div></div></div>'
    ]
    for key, label, cls in (("worst_case", "Worst case", "warn"), ("tested", "Tested", "")):
        if narrative.get(key):
            tiles.append(
                f'<div class="fact {cls}"><div class="k">{label}</div><div class="v">{prose(narrative[key], linker)}</div></div>'
            )
    for fact in narrative.get("facts", []):
        tiles.append(
            f'<div class="fact"><div class="k">{inline(fact.get("label", ""))}</div>'
            f'<div class="v">{prose(fact.get("text", ""), linker)}</div></div>'
        )
    if change.commits:
        items = "".join(f"<li><code>{sha[:7]}</code> {esc(subject)}</li>" for sha, subject in change.commits)
        tiles.append(
            f'<div class="fact"><div class="k">Commits</div><div class="v"><details><summary>'
            f'{plural(len(change.commits), "commit")}, oldest first</summary><ol>{items}</ol></details></div></div>'
        )
    notice = f'<div class="warnbox">{esc(change.notice)}</div>' if change.notice else ""
    return (
        f'<div class="head"><h1>{inline(narrative.get("title", "Review"), linker)}</h1><p class="meta">{"".join(meta)}</p>'
        f'<div class="prose lead">{prose(narrative.get("summary", ""), linker)}</div>{notice}'
        f'<div class="facts">{"".join(tiles)}</div></div>'
    )


def build_review(change: Change, narrative: Dict[str, Any]) -> Tuple[str, int]:
    round_two = narrative.get("feedback") is not None
    if round_two and not change.reviewed:
        raise KitError("The narrative has `feedback`, which needs --since with the previously reviewed head")
    layout = Layout(change)
    linker = layout.linker
    head_label = change.head[:7] if change.head else "uncommitted changes"
    files = len({h.path for h in change.hunks})
    tier, tier_line = pick_tier(narrative, change.hunks, round_two)
    head = header(narrative, change, tier, tier_line, linker)

    sections = decide_cards(narrative.get("decide", []), change, linker, narrative.get("decide_order", ""))
    sections += behavior_table(narrative.get("behavior"), linker)
    sections += claims_section(narrative, change, linker) + reviewers_section(narrative, linker)
    if round_two:
        feedback_html = ""
        for index, item in enumerate(narrative["feedback"], 1):
            fid = str(item.get("id", index))
            where = item.get("where", "")
            tag, label = STATUS_TAGS.get(item.get("status", "changed"), ("", str(item.get("status"))))
            body = layout.entries(item.get("hunks", []), f"your comment {index}")
            panels = "".join(context_panel(ref, change.read) for ref in item.get("context", []))
            on = f", on <code>{esc(where)}</code>" if where else ""
            feedback_html += (
                f'<div class="cm" data-fb="{esc(fid)}" data-where="{esc(where)}" id="fb-{esc(fid)}"><div class="cm-top">'
                f'<div class="cm-q"><span class="who">Your comment {index}{on}</span>'
                f'<div class="txt">{esc(item.get("comment", ""))}</div></div>'
                f'<div class="cm-a"><span class="who">Author <span class="tag {tag}">{esc(label)}</span></span>'
                f'{prose(item.get("reply", ""), linker)}</div>'
                f'</div>{body}{panels}<div class="cm-foot"><button class="linkbtn" data-reply="{esc(fid)}">Reply</button>'
                '<div class="replies"></div></div></div>'
            )
        count = len(change.hunks) - len(layout.placed)
        unasked = layout.groups(narrative.get("groups", [])) + layout.unmentioned()
        sections += (
            f'<section id="unasked"><h2>Changes no comment asked for <span class="count">{count}</span></h2>'
            + (unasked or '<p class="muted">None. Every change answers one of your comments.</p>')
            + "</section>"
            f'<section id="feedback"><h2>Your comments <span class="count">{len(narrative["feedback"])}</span></h2>'
            f"{feedback_html}</section>"
        )
    else:
        diff = layout.groups(narrative.get("groups", [])) + layout.unmentioned()
        order = ""
        if len(change.commits) > 1:
            order = (
                '<span class="seg" role="group" aria-label="Order"><button data-order="reading">Reading order</button>'
                '<button data-order="commit">By commit</button></span>'
            )
        sections += (
            f'<section id="diff"><div class="dhead"><h2>The diff <span class="count">{plural(len(change.hunks), "hunk")} '
            f'in {plural(files, "file")}</span></h2>{order}</div>'
            '<p class="sub">Tap a line to comment on it. Comments stay in this browser until you copy them.</p>'
            f'<div id="reading">{diff or "<p class=muted>No changes.</p>"}</div><div id="bycommit" hidden></div></section>'
        )

    repo = narrative.get("repo") or (change.remotes[0] if change.remotes else "")
    branch = narrative.get("branch") or change.branch
    kind = "Round two" if round_two else "Review"
    brand = f"{kind} <span>{esc(' '.join(x for x in (repo, branch) if x))}</span>"
    body = (
        f'<header class="top"><div class="top-in"><div class="brand">{brand}</div>{TOP_BAR_CONTROLS}</div></header>'
        f'<main class="wrap page">{head}{sections}</main>{BOTTOM_BAR}'
    )
    tree = change.head or f"worktree:{change.diff_hash}"
    key = hashlib.sha1(f"{change.base}:{change.start}:{tree}".encode("utf-8")).hexdigest()[:16]
    span = f"{(change.reviewed or change.base)[:7]}..{head_label}"
    data = {
        "key": key,
        "hunks": {h.id: h.to_page() for h in change.hunks},
        "commits": [[sha[:7], subject] for sha, subject in change.commits],
    }
    title = f"{kind}: {repo.split('/')[-1]} {branch}".strip() if repo or branch else f"{kind}: {span}"
    return page(title, body, ["base.css", "review.css"], "review.js", data), layout.unplaced


def list_hunks(change: Change, as_json: bool) -> str:
    rows: List[Dict[str, Any]] = []
    for hunk in change.hunks:
        first = next((text.strip() for kind, text in hunk.lines if kind != " " and text.strip()), hunk.note)
        rows.append(
            {
                "id": hunk.id,
                "path": hunk.path,
                "old_path": hunk.old_path,
                "changed": hunk.changed("+"),
                "removed_old": hunk.changed("-"),
                "hunk": hunk.range_label,
                "added": hunk.added,
                "removed": hunk.removed,
                "commits": [c[:7] if c != UNCOMMITTED else c for c in hunk.commits],
                "look": hunk.look,
                "first_line": first[:120],
            }
        )
    tier, tier_line = pick_tier({}, change.hunks, bool(change.reviewed))
    if as_json:
        commits = [{"sha": sha[:7], "subject": subject} for sha, subject in change.commits]
        listing = {"notice": change.notice, "tier": tier, "tier_line": tier_line, "commits": commits, "hunks": rows}
        return json.dumps(listing, indent=2) + "\n"
    out = ([change.notice] if change.notice else []) + [f"Lowest tier: {tier}. {tier_line}"]
    for row in rows:
        where = f"{row['path']}:{row['changed']}" if row["changed"] else f"{row['path']} (removed old {row['removed_old']})"
        hunk_range = f"(hunk {row['hunk']})" if row["hunk"] else ""
        out.append(
            f"{row['id']}  {where}  {hunk_range}  +{row['added']} -{row['removed']}  "
            f"{','.join(row['commits']) or '-'}  {row['first_line'][:70]}"
        )
    return "\n".join(out) + "\n"


def decision_sheet(data: Dict[str, Any]) -> str:
    cards = ""
    for number, dec in enumerate(data.get("decisions", []), 1):
        pick, buttons = choices(dec.get("options", []), dec.get("pick"), f"Decision {number}")
        why = f'<p><span class="lbl">Pick {esc(pick)}.</span> {inline(dec["why"])}</p>' if dec.get("why") else ""
        cards += (
            f'<article class="card call dec" data-call="{number}" data-pick="{esc(pick)}">'
            f'<div class="call-top"><span class="num">Decision {number}</span></div><h3>{inline(dec.get("title", ""))}</h3>'
            f'<div class="prose">{why}{prose(dec.get("detail", ""))}</div><div class="opts">{buttons}</div>'
            f'<textarea class="note" aria-label="Note on decision {number}" placeholder="Note (optional)"></textarea></article>'
        )
    body = (
        f'<main class="wrap"><header class="page"><h1>{inline(data.get("title", "Decisions"))}</h1>'
        f'<div class="prose muted">{prose(data.get("intro", ""))}</div></header><div class="decs">{cards}</div>'
        f'<div class="prose">{prose(data.get("ask", ""))}</div></main>'
        '<div class="bar"><div class="tray" id="tray" hidden></div><div class="bar-in"><span class="status" id="status"></span>'
        '<button class="btn primary" id="copy">Copy answer</button></div></div>'
    )
    key = hashlib.sha1(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return page(str(data.get("title", "Decisions")), body, ["base.css", "review.css", "pages.css"], "decisions.js", {"key": key})


def svg_markup(node: ElementTree.Element) -> str:
    tag = node.tag[len(SVG_NS) :] if node.tag.startswith(SVG_NS) else node.tag
    if tag not in SVG_ELEMENTS:
        raise KitError(f"`svg` may not contain <{tag}>")
    attributes = ""
    for name, value in node.attrib.items():
        if name not in SVG_ATTRIBUTES:
            raise KitError(f"`svg` may not use the attribute {name} on <{tag}>")
        if EXTERNAL_URL_RE.search(value):
            raise KitError(f"`svg` may only refer to its own elements, like url(#arrow), not {value!r}")
        if "\\" in value:
            raise KitError(f"`svg` attribute values may not contain a backslash: {value!r}")
        attributes += f' {name}="{esc(value)}"'
    inner = esc(node.text or "") + "".join(svg_markup(child) + esc(child.tail or "") for child in node)
    return f"<{tag}{attributes}>{inner}</{tag}>"


def svg_block(svg: Any) -> str:
    text = str(svg or "").strip()
    if not text:
        return ""
    if "<!" in text:
        raise KitError("`svg` may not contain a doctype, comments, entities or CDATA")
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        raise KitError(f"`svg` must be one well-formed <svg> element: {error}") from error
    if root.tag not in ("svg", SVG_NS + "svg"):
        raise KitError("`svg` must have <svg> as its root element")
    return f'<div class="dg-box">{svg_markup(root)}</div>'


def architecture_page(data: Dict[str, Any]) -> str:
    facts = "".join(
        f'<div class="fact"><div class="k">{inline(f.get("label", ""))}</div>'
        f'<div class="v">{inline(f.get("text", ""))}</div></div>'
        for f in data.get("facts", [])
    )
    sections = ""
    for section in data.get("sections", []):
        sides = ""
        for key, label in (("before", "Before"), ("after", "After")):
            side = section.get(key)
            if side:
                sides += (
                    f'<div class="card side {key}"><h3>{inline(side.get("title", label))}</h3>'
                    f'{prose(side.get("text", ""))}{svg_block(side.get("svg"))}</div>'
                )
        sections += (
            f'<section><h2>{inline(section.get("title", ""))}</h2>{prose(section.get("text", ""))}'
            f'{svg_block(section.get("svg"))}{f"<div class=two>{sides}</div>" if sides else ""}</section>'
        )
    body = (
        f'<main class="wrap"><header class="page"><h1>{inline(data.get("title", "Architecture"))}</h1>'
        f'<div class="prose lead">{prose(data.get("summary", ""))}</div>'
        f'{f"<div class=facts-grid>{facts}</div>" if facts else ""}</header>{sections}</main>'
    )
    return page(str(data.get("title", "Architecture")), body, ["base.css", "pages.css"])


def read_json(path: str) -> Dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise KitError(f"Cannot read {path}: {error}") from error
    if not isinstance(data, dict):
        raise KitError(f"{path} must hold a JSON object")
    return data


def write(path: str, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")
    print(f"Wrote {Path(path).resolve()}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    review = sub.add_parser("review", help="a review page for a diff, or a round two page with --since")
    review.add_argument("--repo", default=".", help="the git repository, default the current folder")
    review.add_argument("--base", help="compare against the merge base of this ref and the head")
    review.add_argument("--head", help="the head commit, default HEAD")
    review.add_argument("--range", dest="span", help="compare exactly A..B instead of --base and --head")
    review.add_argument("--uncommitted", action="store_true", help="include staged, unstaged and untracked changes")
    review.add_argument("--since", help="the head reviewed last round: show only what changed since it")
    review.add_argument("--narrative", help="the narrative JSON file")
    review.add_argument("--list-hunks", action="store_true", help="print the hunk ids instead of building a page")
    review.add_argument("--json", action="store_true", help="with --list-hunks, print JSON")
    review.add_argument("-o", "--output", help="the HTML file to write")
    for name, text in (("decisions", "a decision sheet"), ("architecture", "an architecture page")):
        other = sub.add_parser(name, help=text)
        other.add_argument("input", help="the page JSON file")
        other.add_argument("-o", "--output", required=True, help="the HTML file to write")
    args = parser.parse_args(argv)
    try:
        if args.command == "decisions":
            write(args.output, decision_sheet(read_json(args.input)))
        elif args.command == "architecture":
            write(args.output, architecture_page(read_json(args.input)))
        else:
            repo = Path(args.repo).resolve()
            change = collect(repo, args.base, args.head, args.span, args.uncommitted, args.since)
            if args.list_hunks:
                sys.stdout.write(list_hunks(change, args.json))
                return 0
            if not args.output:
                raise KitError("Pass -o FILE, or --list-hunks")
            narrative = read_json(args.narrative) if args.narrative else {}
            text, unplaced = build_review(change, narrative)
            write(args.output, text)
            if unplaced:
                print(f"{unplaced} of {len(change.hunks)} hunks are not mentioned by the narrative")
    except KitError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
