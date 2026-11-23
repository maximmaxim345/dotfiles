---
name: desk
description: Hand this thread to the desk with an optional note on what to do with it, or pause it until something happens.
argument-hint: "[help | later [when] | <note for the desk> | block <what it waits for>]"
disable-model-invocation: true
---

Arguments: $ARGUMENTS

The desk (`~/desk`, see its `AGENTS.md`) tracks work as backlog items on its board. When `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/api/state` doesn't print 200, stop and tell me.

## Modes

- `help`: show the "Phrases" section from `~/desk/TASK.md` and `~/.claude/skills/desk/help.md` as they are. Then add "For this thread": up to three of those phrases or commands that fit where this thread is now, each with one line why, or say none fits. Stop there, and skip the board check above.
- Nothing: hand this thread to the desk (see "Hand over this thread"). It shows on the board as started, or keeps its paused status when it already has an item, and the desk sweeps it like the threads it started.
- `later`: hand it over paused with `--status open` and no note. Start on the board resumes this thread.
- `later <when>`, like `later next week`, `later in 2 days` or `later friday`: hand it over paused with `--blocked-by 'until <yyyy-mm-dd>'`, the day it names worked out with `date`. Next week is the coming Monday. The desk's morning sweep clears the blocker on that day and resumes this thread.
- `block <what it waits for>`: hand it over paused until that happens. The desk compacts and settles it after this turn. When the blocker clears (GitHub news, a date, or a blocking item finishing), the desk removes it and resumes this thread. A blocker I remove on the board waits for Start.
- Anything else is my note on this thread for the desk. Hand it over and pass the note with `--note`, in my exact words. Also apply what it clearly asks:
  - not now, later, or no time for it: `--status open`, which parks it in the backlog;
  - it waits on something: `--blocked-by "<what>"`, as for `block`;
  - it's finished: `--status done`;
  - drop it or won't do it: `--status dropped`;
  - an effort it belongs to: `--effort <effort>` (see "Effort").

  Do nothing else the note asks, and don't start work on it. The desk reads it and acts or answers on the item.

## Effort

An effort is named by its slug, the folder name under `~/desk/efforts/`. When I name an effort, match it to an existing slug. When none fits, it's a new effort: pick a short lowercase slug (`spec-cleanup`) and say it's new. `bin/backlog adopt` creates its folder.

## Quoting

Pass my words, the blocker and the summary to the commands in single quotes, writing each `'` inside them as `'\''`, so the shell leaves backticks and `$` alone.

## Hand over this thread

1. Take this thread's id from `t3_thread_configuration` without arguments.
2. Commit everything, untracked files included, following my commit rules. Unfinished work goes in a `wip:` commit. Never commit secrets. Nothing is pushed.
3. Write the brief to `~/desk/efforts/<effort>/briefs/<slug>.md`, or to a file under `$TMPDIR` without an effort, since the backlog item keeps its text. Write it for someone who never saw this thread, in the `##` sections "Backlog items" in `~/desk/AGENTS.md` lists, and cover:
   - the goal and the done criteria;
   - the repo, its project rules file, the branch and its base, each commit with one line on what it does, and its PR with its state;
   - what's done and how it was verified, labeled verified or inferred;
   - the next step, and what waits on me (a push OK, a decision, a review), with any draft reply or description I haven't seen yet quoted in full;
   - open questions, approaches rejected and why, and extra findings not filed yet;
   - git-ignored files the work needs, like env files or test data, listed by name.
4. Run:

   ```sh
   ~/desk/bin/backlog adopt --title "<title>" --repo <short repo> [--kind <kind>] \
     --summary '<one or two sentences>' --brief-file <brief path> --thread <thread id> \
     [--pr <PR URL>] [--effort <effort>] [--blocked-by '<what it waits for>'] \
     [--status open|done|dropped] [--note '<my note>']
   ```

   The title is the task without effort or repo prefixes. It prints the item id. When this thread already has an item that isn't done or dropped, it reuses that item and applies only the note, effort, blocker and status. A blocker is added to the ones the item has.
5. Read `~/desk/TASK.md`, which applies to this thread from now on.
6. Reply in one line with the item id and what you applied. Ask nothing, since a question keeps the thread waiting on me and the desk won't settle it.
