# Review kit

`build_review.py` turns a git diff and a small narrative JSON file into one self-contained HTML page. The page inlines its CSS and JavaScript, makes no network requests and works opened straight from disk. It needs Python 3.9 or newer and git 2.40 or newer. With Pygments installed it also colors the code. Run it with `uv run`, which reads the script's header and brings Pygments along. Plain `python3` works too, and the page then has no colors, which the script says in one line.

The script always takes the diff from `git diff`. You never type code into the narrative: it only points at hunks and adds the text around them.

## Commands

```sh
KIT=~/.claude/review-kit/build_review.py

# List the hunks with their ids, to write the narrative against (add --json for JSON)
python3 $KIT review --repo . --base main --list-hunks

# First review: the branch against its merge base with main
uv run $KIT review --repo . --base main --narrative review.json -o review.html

# An exact range, or the working tree (staged, unstaged and untracked files) on top of HEAD
uv run $KIT review --range A..B --narrative review.json -o review.html
uv run $KIT review --base main --uncommitted --narrative review.json -o review.html

# Round two: only what changed since the head Maxim reviewed last
python3 $KIT review --base main --since <reviewed head sha> --list-hunks
uv run $KIT review --base main --since <reviewed head sha> --narrative round2.json -o round2.html

# The two smaller pages
python3 $KIT decisions decisions.json -o decisions.html
python3 $KIT architecture architecture.json -o architecture.html
```

`--base REF` compares the head (default `HEAD`, or `--head REF`) with the merge base of `REF` and the head, like a pull request. `--range A..B` compares exactly `A` with `B`.

`--since` takes the head commit of the last reviewed round. Record its sha when Maxim reviews. The script compares the trees of the old and the new head, so it works whether the fixes are separate commits or the history was squashed, amended or rebased. When the branch moved to a new base, the script first replays the old head onto the new base, so changes that came with the new base stay out. If that replay conflicts, the page says so and compares the two heads directly. The old commit must still exist in the repository (rewritten commits stay until git prunes them).

`--list-hunks` first prints the lowest tier the diff allows (see `tier` below), then one line per hunk: its id, the changed lines (`path:12-30`, counted in the new file), the whole hunk with its context lines (`hunk 9-33`), the added and removed counts, the commits that touched it, and its first changed line. `--json` prints the same as JSON, with `tier` and `tier_line` at the top and `changed` (new-side range of the added lines), `removed_old` (old-side range of the removed lines), `hunk` (the whole hunk) and `commits` per hunk. A `lines` reference matches any hunk it overlaps, so the changed range and the hunk range both work.

The commits of a hunk come from `git blame` over the reviewed range: the commits that added its lines, and for removed lines the commit after the last one that still had them.

The script exits with an error and a message when a reference in the narrative matches no hunk, or when the diff has a line it cannot read. After writing the page it prints how many hunks the narrative does not mention.

## Showing a page

A review page opens from its absolute file path in a browser. Comments and changed picks stay in that browser's storage, and Copy for chat puts the answer on the clipboard for the chat.

In T3 Code, a page that is only looked at, the decision sheet and the architecture page, can also show inline in the thread: check it with `html_preview` on the file path, then pass the path and the `contentHeight` it reports to `html_render`. An inline render has no URL and sends nothing back to the thread, so the answer comes in chat. A review page always goes out as its path, since its comments need a browser.

## The review narrative

Every field is optional. An empty object `{}` gives a page with every hunk under "Not mentioned by the author".

```json
{
  "title": "One sentence: what behaves differently now.",
  "repo": "owner/name",
  "branch": "feat/retry",
  "summary": "Optional paragraphs. Blank lines split paragraphs, `backticks` mark code, web addresses become links.",
  "worst_case": "What breaks, for whom, if this change is wrong.",
  "tested": "What ran and what did not.",
  "tier": "normal",
  "tier_reason": "Why this tier, in one line.",
  "meta": ["draft PR 42"],
  "facts": [{"label": "After your go", "text": "The agent marks the PR ready."}],
  "decide_order": "in the plan's order",
  "decide": [
    {
      "title": "Keep the retry loop?",
      "risk_level": "medium",
      "undo": "Cheap to reverse",
      "risk": "What goes wrong if the pick is wrong.",
      "evidence": "What the pick rests on.",
      "refs": [{"file": "src/client.py", "lines": "40-52"}],
      "context": [{"file": "src/store.py", "lines": "10-20", "note": "the caller"}],
      "pick": "A",
      "why": "One line why the pick.",
      "options": [{"text": "Keep it."}, {"text": "Drop it."}, {"id": "C", "text": "Move it."}]
    }
  ],
  "behavior": {
    "rows": [{"case": "The server restarts.", "before": "The client stays offline.", "after": "The client reconnects."}],
    "unchanged": "What stays the same that a reader might expect to change."
  },
  "claims_note": "Tests ran in a fresh clone.",
  "claims": [
    {"claim": "The client reconnects after a server restart.", "proof": "test", "name": "test_reconnect_after_restart",
     "fails_without": true, "refs": [{"file": "tests/test_client.py", "lines": "40-60"}]},
    {"claim": "The other client tests still pass.", "proof": "run", "name": "uv run pytest tests/test_client.py", "detail": "62 passed"},
    {"claim": "It works on a real speaker.", "proof": "none", "detail": "No hand test yet."}
  ],
  "reviewers_note": "Optional line, such as which reviewers did not run.",
  "reviewers": [
    {"name": "Copilot", "fixed": ["The retry loop never gave up."], "kept": [{"finding": "Retry forever.", "why": "The caller sets a deadline."}],
     "skipped": 2}
  ],
  "groups": [
    {
      "title": "Core",
      "note": "Optional text under the group title.",
      "hunks": [
        {"hunk": "h1a2b3c4d", "note": "Why this hunk matters.", "look": "decide 1",
         "context": [{"file": "src/store.py", "lines": "10-20", "note": "what it calls"}]},
        {"file": "src/client.py", "lines": "80-95", "note": "The fallback."},
        "h5e6f7a8b"
      ]
    },
    {"unimportant": true, "reason": "Import order only", "hunks": [{"file": "src/__init__.py"}]}
  ]
}
```

- `tier` is one of `fixup`, `small`, `normal`, `risky`. The script computes the lowest tier from the size of the diff (changed lines outside tests: over 400 is risky, 50 or more is normal, otherwise small, and fixup only in round two at 15 or fewer). A hunk in a path marked for a close look (see below) makes it at least normal. The narrative may raise the tier, never lower it. Leave it out to take the computed one.
- `repo` and `branch` name the page in the browser tab and the top bar. Without them the page takes the repository from the `upstream` or `origin` remote and the branch from `--head` or the end of `--range`, never from the checkout's folder or its current branch.
- `worst_case` and `tested` sit next to the tier at the top, as do the `facts`.
- `decide` cards come first on the page, in the order given. The heading shows their count, followed by `decide_order` when set (for example "riskiest first"). See "Decide cards" below.
- `claims` lists each behavior the change claims, with its `proof`: `test`, `run` (a command and its result), `recording` or `none`. `name` is the test, the command or the recording, `detail` adds the result. For a test, `fails_without` says whether it fails without the change (`true`), passes without it (`false`) or was not tried (left out). Claims without proof are marked. `refs` link to hunks as on decide cards.
- `reviewers` gives one line per reviewer: what it found that was fixed (a list, or a count), what was kept and why, and how many theoretical findings were skipped. Each of the three counts shows only when its field is given. `note` adds text to a reviewer, such as the findings of your own pass. `reviewers_note` shows even without reviewers.
- `groups` set the reading order. A group is shown in full, or collapsed under its one-line `reason` when `unimportant` is true. A collapsed group takes no `note`: put it on one of its hunks. Every hunk the groups do not place appears in a last group, "Not mentioned by the author". Nothing is dropped.

### Paths to look at closely

`review-paths.json`, next to the script, lists per repository the paths that need a close look however small the change. It names the contracts of each project, such as stored data, settings, shared models and text users see, and the rule text agents read in this repository. A hunk whose file matches gets a "Look closely" tag with the reason, a collapsed group says how many of its hunks have one, and the tier is at least normal. It is a narrower, mechanical subset of the "Always look closely" list in a project's rules file, which an author still applies by hand.

```json
{"music-assistant/server": {"music_assistant/models/**": "the shared models", "**/strings.json": "text users see"}}
```

The key is the `owner/name` of the `upstream` or `origin` remote, in any case. A pattern matches the whole path: `*` and `?` stay within one folder, `**` crosses folders.

### Decide cards

A decide card asks Maxim one question that has a pick. Its fields:

- `title`: the question, short enough to scan.
- `risk_level`: `low`, `medium` or `high`, how much goes wrong if the pick is wrong. Shown as a tag.
- `undo`: how hard the pick is to reverse later, such as "Two-way door" or "Needs a migration". Shown as a tag. Leave it out when `risk` already says it.
- `risk`: what goes wrong, and for whom, if the pick is wrong.
- `evidence`: what the pick rests on, such as a test, a measurement or a line of code. Write `path:line` and the page links it to that line.
- `refs`: hunk references (see below) that the question is about. Each becomes a link that opens the hunk, scrolls to the lines and marks them.
- `context`: unchanged code the question needs, shown on the card.
- `options`: the choices, each `{"text": ...}` with an optional `id`. Ids default to A, B, C.
- `pick`: the id of the recommended option. `why`: one line why.

### Hunk references

A hunk entry is one of:

- a hunk id from `--list-hunks`, as a string or as `{"hunk": "h1a2b3c4d"}`. The id is a hash of the file path and the changed lines, so it stays the same when other hunks change.
- `{"file": "path", "lines": "80-95"}`: the hunks of that file that overlap those lines, counted in the new version of the file.
- `{"file": "path"}`: every hunk of that file that no earlier entry placed.

An entry object can add `note` (text above the hunk), `look` (a "Look closely" tag, `true` or a short reason) and `context`. When an entry resolves to several hunks, `note`, `look` and `context` go on the first. A hunk placed twice is shown once, and the later place gets a link to it.

### Context references

`{"file": "path", "lines": "10-20", "note": "optional"}` shows unchanged lines from the head commit (or the working tree with `--uncommitted`) in a panel. Use it for code a reader needs to understand a hunk or a decision.

## The round two narrative

A round two narrative has a `feedback` list and needs `--since`. Hunks here are hunks of the diff since the reviewed head, so list them with the same `--since`.

```json
{
  "title": "Two of your three comments changed the code.",
  "feedback": [
    {"comment": "should a zero also be skipped?", "where": "app.py:94", "status": "changed",
     "reply": "Yes, `total` now skips `0` too.", "hunks": [{"file": "app.py", "lines": "94-96"}]},
    {"comment": "why read OFFSET here?", "where": "app.py:176", "status": "declined",
     "reply": "It mirrors how callers configure offsets.", "context": [{"file": "app.py", "lines": "174-177"}]}
  ],
  "groups": [{"title": "Formatting", "unimportant": true, "reason": "Black reflowed one call", "hunks": ["h0badc0de"]}]
}
```

- `comment` is Maxim's comment as he wrote it, `where` the `path:line` it was on.
- `status` is `changed`, `partly` or `declined`. `reply` says what changed or why nothing did.
- `hunks` are the changes that answer the comment. `context` shows code that did not change.
- `groups` and every hunk no feedback item claims appear on top, under "Changes no comment asked for".
- `decide` and `behavior` work as in a first review.

## What the page does

- Decide cards first, then the before and after table, the claims and what the reviewers found, then the diff in reading order with each note above its hunk. When the range has more than one commit, a By commit switch regroups the same hunks under the commit that touched them, oldest first, and each hunk shows its commits.
- A `path:line` or `path:10-20` in any text of the narrative links to that line when the page shows it, inside a hunk or in its unchanged lines. A path may be shortened to its end, like `worktree-due:40`, as long as only one changed file ends that way. Following such a link or a card ref opens the hunk, reveals the lines and marks them.
- Side by side diff on screens 900 pixels and wider, stacked below that, with syntax colors and word-level highlights inside changed lines. The colors come from Pygments at build time, from the whole old and new file, so a line inside a multi-line string is colored as a string. The top bar switches between Auto, Side by side and Stacked.
- A carriage return shows as a small ␍, and a line without a final newline carries a "No newline at end of file" note, so a change of line endings is visible.
- Markdown and text files open in a Words view that shows the changed paragraphs with struck and marked words. The source text stays raw. Long lines wrap with a hanging indent under list markers. A Lines switch shows the usual diff. These files show no function line in the hunk header.
- Wrap lines is off by default, so long lines scroll inside the diff. Side by side, each side scrolls on its own. A shadow on the right edge and a "scroll sideways" note in the hunk header show when lines continue. The choice is remembered in the browser.
- Each hunk can show up to 100 unchanged lines above and below it, 20 per click, like GitHub.
- Tapping a line, a word block or the Comment button on a hunk opens a comment box. Round two pages add a Reply button per feedback item. Comments and changed picks stay in the browser's local storage for that diff. Copy for chat puts the answer on the clipboard for pasting into the chat: `go` when no pick changed and there are no comments, otherwise the changed picks like `2B, 4C` followed by each comment as `path:line: text`.
- Light and dark follow the system setting. At phone width only the diff scrolls sideways.

## Decision sheet

```json
{
  "title": "Three choices for the cache rework",
  "intro": "Optional text.",
  "decisions": [
    {"title": "Where does the cache live?", "pick": "A", "why": "One owner keeps invalidation in one place.",
     "detail": "Optional longer text.",
     "options": [{"text": "In the store."}, {"text": "In each caller."}, {"text": "In a new service."}]}
  ],
  "ask": "Optional closing line."
}
```

Copy answer puts `go` on the clipboard when every pick is kept, otherwise the changed ones like `2A, 3C`, followed by any notes typed under a decision.

## Architecture page

```json
{
  "title": "Move the cache into the store",
  "summary": "Optional text.",
  "facts": [{"label": "Undo", "text": "Two-way"}],
  "sections": [
    {"title": "Structure", "text": "Optional text.", "svg": "<svg ...>...</svg>",
     "before": {"title": "Before", "text": "Two caches.", "svg": "<svg ...>...</svg>"},
     "after": {"title": "After", "text": "One cache.", "svg": "<svg ...>...</svg>"}}
  ]
}
```

`svg` is one inline `<svg>` element of shapes and text. The script rebuilds it from a fixed list of SVG elements and attributes and refuses anything else, such as scripts, event handlers, links, images, `style`, comments, backslashes and references outside the drawing (`url(#arrow)` is fine). Give it a `viewBox` so it scales, and add `class="wide"` to keep a wide diagram readable on a phone (it then scrolls sideways). These classes follow light and dark mode: `box` on a `rect` (with `new`, `chg` or `del`), `edge` on a `path` or `line` (with `new`, `chg`, `del` or `accent`), and `muted` on `text`. Plain `text` uses the page's text color.
