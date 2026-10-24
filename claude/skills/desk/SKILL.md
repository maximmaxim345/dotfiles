---
name: desk
description: Hand this thread to the desk with an optional note on what to do with it, pause it until something happens, or move Claude desktop sessions to T3 Code threads.
argument-hint: "[<note for the desk> | block <what it waits for> | move [which sessions, in any words] [into <effort>]]"
disable-model-invocation: true
---

Arguments: $ARGUMENTS

The desk (`~/desk`, see its `AGENTS.md`) tracks work as backlog items on its board. When `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/api/state` doesn't print 200, stop and tell me.

## Modes

- Nothing: hand this thread to the desk (see "Hand over this thread"). It shows on the board as started, and the desk sweeps it like the threads it started.
- `block <what it waits for>`: hand it over paused until that happens. The desk compacts and settles it after this turn. Once I remove the blocker on the board and press Start, the desk resumes this thread.
- `move`, alone or followed by which sessions to move and optionally an effort, in any words: move Claude desktop sessions to T3 Code threads (see "Move desktop sessions").
- Anything else is my note on this thread for the desk. Hand it over and pass the note with `--note`, in my exact words. Also apply what it clearly asks:
  - not now, later, or no time for it: `--status open`, which parks it in the backlog;
  - it waits on something: `--blocked-by "<what>"`, as for `block`;
  - it's finished: `--status done`;
  - drop it or won't do it: `--status dropped`;
  - an effort it belongs to: `--effort <effort>` (see "Effort").

  Do nothing else the note asks, and don't start work on it. The desk reads it and acts or answers on the item.

In the Claude Code desktop app (you have the `mcp__ccd_session_mgmt__*` tools), the desk can't track or resume this session. There, nothing means `move` for this session alone. `block` and notes aren't available: say so and stop.

## Effort

An effort is named by its slug, the folder name under `~/desk/efforts/`. When I name an effort, match it to an existing slug. When none fits, it's a new effort: pick a short lowercase slug (`spec-cleanup`) and say it's new. `bin/backlog` creates its folder.

## Quoting

Pass my words, the blocker and the summary to the commands in single quotes, writing each `'` inside them as `'\''`, so the shell leaves backticks and `$` alone.

## Hand over this thread

1. Take this thread's id from `t3_thread_configuration` without arguments.
2. Commit everything, untracked files included, following my commit rules. Unfinished work goes in a `wip:` commit. Never commit secrets. Nothing is pushed.
3. Write the brief as in step 4 of "Prepare" below.
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

## Move desktop sessions

For each task this moves, usually one per session, the desk starts a T3 Code thread on the same branch with a brief the session wrote. A session is archived only after the T3 threads for all its tasks confirmed their branch, so nothing is lost when a launch fails.

### Which sessions

Read the words after `move` freely, as numbers, names, descriptions or a mix:
- No sessions named: move this session alone. Do "Prepare", "Hand over" and "Archive" for it yourself.
- Task sessions named: this session coordinates an effort in `~/desk/efforts/<effort>/status.md`. Match my words to the tasks in its table and move those. `all` means every active task session in its table, and then this session last as the effort's manager.
- `archive`: do only "Archive", for items moved earlier whose sessions are still active (`~/desk/bin/backlog list` and the items' `move` fields).

The words may also name an effort ("into spec-cleanup", "as a new effort for the docs"). The moved sessions go into it (see "Effort"). Without one, a moved task keeps its coordinator's effort, and a single session keeps the effort its brief names, if any. When a coordinator moves itself into another effort, its T3 thread manages that effort.

List the sessions you'll move with their branches and PRs, and the effort, marked new when it is. Then wait for my OK.

### Prepare

A coordinator sends each task session "Prepare to move to T3 Code: follow the Prepare steps in `~/.claude/skills/desk/SKILL.md` and reply with their result line." with SendMessage, and waits for every reply. Each session then:

1. Stops after its current step and starts nothing new.
2. Lists every branch it worked on, in every repo it touched, with its worktree (`git worktree list` in each repo) and its PR. Each branch becomes a task of its own, since a T3 thread shows only its own branch. Leave out branches with nothing left to keep (merged, or abandoned experiments), and name them in the brief of the task they relate to.
3. Commits everything in each of those worktrees, untracked files included, following my commit rules. Unfinished work goes in a `wip:` commit. Never commit secrets. Nothing is pushed.
4. Writes one brief per task to `~/desk/efforts/<effort>/briefs/<slug>.md`, or to a file under `$TMPDIR` without an effort, since the backlog item keeps its text. Write it for someone who never saw this session:
   - the goal and the done criteria;
   - the repo, its project rules file, the branch and its base, each commit with one line on what it does, and its PR with its state;
   - the other tasks from this session and which of them this one builds on;
   - what's done and how it was verified, labeled verified or inferred;
   - the next step, and what waits on me (a push OK, a decision, a review), with any draft reply or description I haven't seen yet quoted in full;
   - open questions, approaches rejected and why, and extra findings not filed yet;
   - git-ignored files the work needs, like env files or test data. Copy them to `~/desk/efforts/<effort>/work/<slug>/`, which git ignores, or next to the brief without an effort, and list them by name. Archiving removes the old worktree with everything in it.
5. Frees every branch once `git status --porcelain` prints nothing in its worktree: `git switch --detach` in a worktree, or a switch to the default branch in a main checkout. `git worktree list` must no longer show any of them. When something is still uncommitted, stop and report it instead. Skip this step when the session has no branch of its own.
6. Replies with one line per task: `<title> | <short repo> | <kind> | <branch or none> | <PR URLs separated by spaces, main first, or none> | <brief path> | <main checkout> | <session id>`. The title is the task title without its number and type, a main checkout is the parent of `git rev-parse --path-format=absolute --git-common-dir`, and the session id comes from `get_session` on `self`.

### Hand over

When a session replied with more than one line, show me those lines and wait for my OK. On a no, ask it to drop the branches I named and reply again.

For each line, run:

```sh
~/desk/bin/backlog move --title '<title>' --repo <short repo> --kind <kind> \
  --summary '<one or two sentences>' --brief-file <brief path> --session <session id> \
  --checkout <main checkout> [--branch <branch>] \
  [--pr <PR URL> ...] [--effort <effort>]
```

Repeat `--pr` for each PR, the main PR first. It adds the backlog item, presses Start for it and prints its id. The desk then starts the T3 thread on that branch.

A coordinator moving itself goes last. First it brings the "Resume here" part of `status.md` up to date, including which session moved to which item, and writes a brief that points to `status.md`. Then it runs the command with `--manager` and without `--kind`, `--branch` or `--checkout`. Its T3 thread becomes `manager - <effort>` and rewrites `status.md` in the desk's format, into the new effort's folder when it moved into one.

### Archive

Run `~/desk/bin/backlog wait-moved <item ids>` as a background Bash command (`run_in_background`, timeout 7200000). It returns once every item has a thread, the desk stopped it because it needs me, or I took it back on the board before it started. It prints `<session id> <thread id>` for each item with a thread, `stuck <item id> <session id>: <what I must do>` for each stopped one, `held <item id> <session id>: <status>` for each one I took back, and `timeout <item ids>` for items still pending after about two hours.

- Archive each session once with `archive_session` when all its items have a thread. That also removes its old worktree, which nothing uses anymore. Archive this session last, and only when all its items have a thread.
- Leave every other session as it is, since a `held` or `stuck` session still holds its work. After I pressed Start for a `held` item, or did what a `stuck` line asks and pressed Start, `/desk move archive` archives the rest.

Then reply with one line per item: its title and its T3 thread id, or what it needs from me.
