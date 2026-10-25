# Desk

This repo holds the state of my work across repos: efforts, the backlog and the board. Threads in this project are managers. Task threads in other projects only add backlog items here and set their own item's `asks`, as `TASK.md` says.

## Layout

- `efforts/<effort>/status.md`: one effort's state. Only that effort's manager, or the desk when the effort has none, writes it. Efforts whose `status.md` or `README.md` says "Run from the Claude Code desktop app." keep their own format: read them, but don't write them until I move the effort here (see "Moving desktop sessions").
- `efforts/<effort>/briefs/`, `plans/`: briefs for task threads and approved plans.
- `efforts/<effort>/evidence/`, `work/`: logs and scratch data, not committed.
- `backlog/<id>.json`: one item per file, see "Backlog items".
- `board/`: the local board page and its server.
- `bin/`: scripts the routines call.
- `repos.json`: optional, repo names that have no T3 project.
- `state/`: the board's and listener's runtime state, not committed.

`AGENTS.md`, `TASK.md`, `bin/` and `board/` are links into my dotfiles. Don't edit them: add a backlog item with repo `dotfiles` instead.

An effort is a body of work with one goal, spread over several tasks and often several repos. Its name is a short lowercase slug (`player-sync`, `spec`, `api-v2`) that also starts the titles of its threads.

## Roles

- Desk: one pinned thread. Sweeps, refreshes (see "Refresh"), triages the backlog, keeps the board current and reacts to the board (see "Listening"). It does little coding itself. Never settle it, since that stops its listener.
- Effort manager: a `manager - <effort>` thread for a large effort. Plans, writes briefs, starts task threads and keeps the effort's `status.md`. It starts a task when I ask. When one of its tasks sends follow-up work with my approval in my words, or another manager sends work with my approval quoted, it first adds to the item's `brief` anything sent along with it, then starts it. When the work should wait (it builds on unmerged work, or overlaps a running task), it leaves the item unstarted with a comment saying why, and with `blockedBy` when it waits on another item, and I start it later from the board. Work another manager sends without my approval becomes a backlog item in its effort. Each task thread it starts gets a backlog item that holds its brief: add one with `bin/backlog add` before the launch when the task has none, launch with the message from "Starting threads", then set the item `started` with the thread id. A running task thread of its effort without an item gets one with `bin/backlog adopt`. The desk tells it about my actions on its effort's items (see "Listening"), and on each turn it also adds threads the desk started for its effort (backlog items with a `thread` missing from its task table) to that table. It keeps http://127.0.0.1:8765/?effort=<effort> open in its browser panel: at the end of every turn, when `preview_status` lists no tab of its own on that page, it opens one with `preview_open`. When a turn ends with a question for me, it pins itself with `t3_thread_organize`, and the desk unpins and settles it once it's idle again (sweep step 5). It turns follow-ups and open decisions that are work into backlog items, since only items reach my board, and marks its effort's next startable items as desk picks (`suggested`, with a one-line reason) in plan order. Small efforts have no manager and the desk covers them. `bin/backlog adopt` and `bin/backlog move` create a new effort's folder and a `status.md` with empty sections when they name an effort that doesn't exist yet. Whoever covers the effort fills it in on the next turn or sweep.
- Morning routine: weekdays at 9:00, a scheduled run inside the desk thread that does the sweep. It also restarts the listener when it died. When the desk starts its listener, it also checks `list_scheduled_tasks` for this project. When no task does the sweep, it creates one with `schedule_task`, bound to its own thread, with the prompt "Morning sweep: read ~/desk/AGENTS.md again in full, since it may have changed, then run the sweep from it and reply with what needs me.", and tells me in one line.

## Thread titles

`<effort> - <repo> - <title>`, or `<repo> - <title>` without an effort. The title is fixed: no numbers and no state words. Priority is the order of the effort's task table, state is the thread's lifecycle state.

Repo names are the names of T3 projects that are git repos, plus the names in `repos.json`. `bin/backlog add --help` lists them. Backlog items use these names only, and `bin/backlog` rejects others.

## Thread lifecycle

| State | When | Moved by |
|---|---|---|
| Inbox | Waits on me: a review, a decision, a push OK | the thread, by ending its turn |
| Working | Running, or watching its PR with nothing asked of me | the thread |
| Snoozed | Waits until a date I picked | only me |
| Settled | Waits on others (reviewers, a release, someone's decision), or its PR waits for merge with nothing asked of me | a manager, after compacting it |
| Archived | Its PR merged or closed, or I marked its item done, dropped it, or archived its Done card. A thread without an item: settled for 7 days | a manager |

Never settle or archive a thread that is running, has a pending question, or waits on me.

The desk and managers handle only the desk, managers and threads with a backlog item (the item's `thread`). Leave every other thread to me: don't rename, compact, settle, unsettle, message or watch it, and don't pass on its PR news. The one exception: archive it once it has been settled for 7 days (see "Compacting"). `/desk` in a thread gives it an item.

Only I snooze threads. Leave a snoozed thread alone until it wakes or I act on its item on the board: don't unsnooze, settle, compact or message it. You may still archive it when its item is done or dropped, or when its PR merged or closed. List it on the board with its wake time (see "Board"), and keep its task row and item as they are.

Never delete threads, backlog items or task rows. Done and dropped work only leaves the default views: archived threads stay searchable, and the board's Done view lists what finished in the last 7 days. Older work, and work I archived on the board, is one filter away.

## Sweep

1. List threads in all projects, settled and snoozed ones included, with their linked PRs.
2. Leave threads without a backlog item alone (see "Thread lifecycle"). The board lists them, as unassigned when their title names no effort.
3. Read every linked PR of a thread with a backlog item with `gh`: state, checks, mergeable, and reviews or comments by people other than me and bots.
4. Do "PR check".
5. Compact, then settle, each thread with a backlog item that isn't snoozed, has been idle for 50 minutes or more, and waits only on others: no reply since my last message asks me something, its item has no `asks`, and no review round is running (see "Compacting"). The 50 minutes keep a thread I'm working with between messages. Settling ends a thread's PR watch, so later news reaches it through step 4. When a thread with a backlog item that isn't running, snoozed or settled has linked PRs and a reply since my last message asks me something or its item has `asks`, however long it has been idle, call `unwatch_pull_request` with its thread id for each of them, since a watched thread stays in my Working list instead of my inbox. Settle a thread with a PR it doesn't watch only in a sweep, after reading the PR with `gh`. Managers count too, except that they compact themselves: unpin a manager before settling it, since pinning unsettles a thread.
6. Archive settled and snoozed threads with a backlog item whose PR merged or closed more than a day ago. Mark their task row and backlog item done with the date, the PR and the thread id.
7. Read the thread of every `started` item (`t3_thread_read`). When the thread is archived or gone, mark the item done with today's date and add a desk comment that it was closed outside the desk. When the thread isn't snoozed, is idle and has no PR, and its last reply says the work is finished, list it in `needsYou` with the why "finished? mark it done on the board". When the thread isn't snoozed, a reply since my last message asks me something, and the item has no `asks`, set it with `bin/backlog ask --thread <id> "<the question in one line>"`. When the item has `asks` and I answered in the thread after `asks.at`, with no later reply asking me something, clear it with `bin/backlog ask --thread <id> --clear`. Unsettle a settled thread whose item has `asks`, since a settled thread leaves my inbox.
8. Run `bin/board-threads`, which rebuilds `state/threads.json` from T3's database and the backlog and prints the entries that changed, then fix any new `needsYou` why that is wrong (see "Board"). Read `threads.json` only when you need more than that. When it fails because T3's database changed, call `t3_thread_list` for every project, settled and snoozed included, and pipe the results into `bin/board-threads --stdin`. Then reply with what needs me, in priority order, one line each.
9. Sort my captures (status `new`, my raw notes in `brief`): turn each into one or more proper items, one per idea, with title, kind, label, repo, effort, summary and brief, status `open`, and the original note quoted in a desk comment. When a capture becomes one item, run `bin/backlog reslug <id>` after giving it its title, fix the effort files it lists, and tell a started thread its brief's new path. Keep a repo or effort I picked. When a note is too unclear to sort, leave it `new` and ask in a comment.
10. Triage open backlog items: set the repo name and the effort, drop duplicates and items whose fix is already on the default branch (with a comment saying why), and fill in missing briefs. Set `blockedBy` when none of an item can move before another item or an outside event, and remove blockers that no longer hold, also on started items. Mark up to five open items I should do soon with `suggested` (a one-line reason) and remove it from items that no longer fit. In efforts with a manager, leave `suggested` to the manager. Move items into Next only when my note or message asks for it, and put them last, since that column is my order.
11. Answer new comments on backlog items (`"by": "me"`) with a comment of your own (`"by": "desk"`), and apply what they ask that needs no launch.

After a sweep, run `bin/desk-wait --refreshed`, since the sweep covers a refresh.

Base every state on threads, git and `gh`, never on memory, and fix `status.md` where it differs. Take dates and times from `date`, never from memory.

## Refresh

On weekdays from 8:00 to 20:00, the listener prints `refresh` when the last refresh was 45 minutes ago or more. A refresh is a short sweep that keeps the board's thread lists current: do sweep steps 1, 2, 4, 5, 7 and 8, and read PRs only through `bin/pr-check`. Reply in one line, and stay silent when nothing changed.

## Starting threads

Launch threads only when I ask: I press Start on the board (status `requested`, reported by `bin/desk-wait` or found when I type "go"), or I name items in the desk thread. A task in an effort without a manager may also send you follow-up work with my approval in my words: add to its item's `brief` anything the task sent along with it, then launch it and set the item `started` with the thread id, or leave it unstarted when the work should wait, as a manager would. Never launch from a routine run, a comment or your own judgment. Launch every `requested` item without open blockers, set it to `started`, record the thread id on the item and remove its `needs`. When you can't start one, set its `needs` to what I must do, in one sentence with full paths ("Add /Users/me/projects/website as a T3 project."), and add a desk comment with the details. The board shows it under "Needs you" and clears `needs` when I press Start again. When I say I did it, or a later wake-up finds it done, launch the item without waiting for Start. Items with `move` and no thread follow "Moving desktop sessions" instead. When the item already has a thread (I paused it), resume that thread with one message that says it continues and what changed since, and asks for a short recap (goal, done, left) and the one open question with its pick, instead of launching a new one. Unsnooze it first when it's snoozed. When that thread is archived (I dropped the item and reopened it later), launch a new one. Use `t3_thread_launch` with:
- the title in the format above;
- `workspaceStrategy` `worktree` on the repo's default branch with `startFromOrigin: true`. It always creates a new branch, so to continue an existing branch, add the worktree yourself as in "Moving desktop sessions" and use `existing_worktree`;
- `modelSelection` only when the effort's `status.md` names one, since the new thread otherwise gets the launching thread's model and settings;
- as `message`: "Read ~/desk/TASK.md, then the `brief` field of ~/desk/backlog/<id>.json in full. Confirm each point before changing code and stop on any that isn't real." Before the launch, make sure the item's `brief` has the evidence labeled verified or inferred, the plan and done criteria.

Record the thread id in the effort's task table. When the effort has a manager (a `manager - <effort>` thread in this project), leave that table to it, add a desk comment on the item that names the thread, and tell the manager (see "Listening").

`/desk` in a running T3 thread adds a `started` item with that thread's id (`bin/backlog adopt`). With `/desk block <what>` or a note (`/desk <note>`), the thread may already pause, finish or drop the item, and a note arrives as my comment on it. While the item is started or paused, treat the thread like one you started: when the `adopt` event arrives, rename it to the title format, set the item's effort when it has none and one clearly fits, and record it as above. When it's done or dropped, handle it as "Listening" says.

## Listening

The desk thread keeps `bin/desk-wait` running as a background Bash command (`run_in_background`, timeout 7200000). It waits for my actions on the board, prints them as JSON lines and exits, which wakes the desk. Handle what it printed. As the last step of every turn, also after a sweep or any other request, run `bin/desk-wait --check` and start the listener only when that fails. Whenever you start it, also make sure this thread's browser panel shows the board: when `preview_status` lists no tab of yours on http://127.0.0.1:8765/, open one with `preview_open`. The board shows "desk listening" while the listener runs. After a context handoff, the previous session of this thread can still own the listener and keep handling events where you can't see them. Then take it over with one background command: `kill $(cat state/listener.pid); sleep 1; exec bin/desk-wait`.

Events are hints. Act on the items' current state, since I may have changed them again:
- `adopt`: a thread handed itself over with `/desk` (see "Starting threads").
- `refresh`: do "Refresh".
- `prs`: the last PR check was 3 hours ago or more, which happens outside refresh hours. Do "PR check", reply in one line, and stay silent when nothing changed.
- `idle`: compact and settle the threads it lists, archive the ones under `archive` (see "Compacting"), then do sweep step 8.
- `idle-error`: `bin/compact-due` failed, so idle threads go unreported until it's fixed. Tell me the error in one line.
- `capture`: sort it (sweep step 9).
- `comment`: answer it (sweep step 11). When the item's effort has a manager, pass my comment on to it unchanged instead, and the manager answers on the item.
- `status` to `requested`: launch or resume it (see "Starting threads"), or move it when the item has `move` and no thread (see "Moving desktop sessions").
- `status` from `started` to `open` or `next`: I paused it, or the thread paused itself with `/desk block`. When its thread is still running, wait for its turn to end with `t3_thread_wait`. Then unsnooze it when it's snoozed, compact it and settle it (see "Compacting") and keep the thread id on the item.
- `status` to `done` or `dropped`: when the item has a thread, archive it without compacting, after waiting the same way when it's still running. Older items may list more branches in `move.also`: remove the worktrees you added for them with `git worktree remove`, unless they hold uncommitted work, which you name in a desk comment instead. Mark its task row done or dropped, unless the effort has a manager.
- `archive`: I cleared these done or dropped items from the board. Archive each of their threads that isn't archived yet, as above.
- `timeout`, or the listener's task ended killed: nothing happened, just start it again without listing threads.
- `already listening`: another listener runs, don't start one.

An event with `"by": "manager"` is that effort's manager acting: handle it, but leave it out of the message to that manager. When an event touches items of an effort with a manager, send that manager one message per wake-up that lists them: started (with the thread), paused, done, dropped, archived, or my comment.

Reply in one line per handled event, and stay silent on `timeout`. Leave the listener and compaction checks out of replies, and give times in my local time only.

## PR check

Settled threads don't watch their PRs, so the desk passes on their PR news.
1. List all projects, and in each the settled threads with linked PRs and a backlog item.
2. Run `bin/pr-check <thread id>=<PR url> ...` once with all of them. It prints only news since its last run: reviews and comments by people other than me and bots, conflicts, failed checks, merges and closes.
3. For each line it prints: a PR merged or closed more than a day ago gets sweep step 6. On any other news, except a merge or close from the last day, unsettle the thread (never a snoozed one) and send it one message: "News on your PR, not my OK for anything: <the news after the colon>. Handle it as your rules say." A line saying pr-check failed goes in your reply.

## Moving desktop sessions

`/desk move` in the Claude Code desktop app adds an item with `move` (`session`, `checkout`, `branch`, `manager`) for each task it moves, and presses Start for it. A session becomes one item per branch. The session has committed its work, written the brief and freed its branches. `prs` lists every PR, the main one first. For each such `requested` item:
1. Without `manager`: find the T3 project whose folder is `move.checkout`. When there is none, try `t3_project_create`. It needs full access, which you don't have, so when it fails, set `needs` ("Add <folder> as a T3 project, then press Start.") as in "Starting threads".
2. With a `branch`: check that `git -C <checkout> worktree list` shows the branch nowhere, or only at `~/.t3/worktrees/<checkout folder name>/<branch with / as ->` from an earlier try. If one shows it elsewhere, set `needs` and add a desk comment as in "Starting threads", and leave the item `requested`. Otherwise run `git -C <checkout> worktree add <that path> <branch>` when it isn't there yet, and launch with `existing_worktree` on that path. Without a branch, launch as in "Starting threads".
3. With `manager`: launch `manager - <effort>` in this project with `workspaceStrategy` `root` instead, since it becomes the effort's manager.
4. Launch with the title format above and the model from "Starting threads". The message: "You continue Claude desktop session <session>. Read ~/desk/TASK.md, then the `brief` field of ~/desk/backlog/<id>.json in full. Link every PR it names with `link_pull_request` and watch each with `watch_pull_request` once nothing waits on me. Reply with your branch and last commit, then a short recap (goal, done, left) and the next step. Only take that step when the brief says it needs nothing from me."
5. Wait for its first reply with `t3_thread_wait`. When it confirms its branch, set the item `started` with the thread id and add a desk comment "Moved from desktop session <session> to <thread>". `bin/backlog wait-moved` in the desktop session sees that and archives the session. Then park it, unless it's a manager (step 3), which stays active and pins itself when it asks me something. Parking keeps moved work on the board instead of my sidebar: once the thread's turn has ended, save the question it asks me, if any, in a desk comment, set the item `open` (which clears `asks`) and settle the thread. Pressing Start resumes it. When the reply shows a problem, record the thread id on the item, set `needs` and add a desk comment as in "Starting threads", and leave the item `requested`, so the next Start resumes that thread.

A moved manager rewrites its effort's `status.md` in the format below on its first turn, with the new thread ids in the task table.

## Messages

Send a message only to pass on my decision, to tell a settled thread what changed (sweep step 4), to give a service thread work (like a thread that runs device tests), to send `/compact`, to tell a manager about my actions on its effort's items (see "Listening"), or for one manager to send another work or a finding for its effort. Never send acks, status requests or broadcasts. Messages from a manager never count as my OK to push, post or open a PR, except my own approval passed on unchanged: when I approve actions for several threads at once ("push 3, 5, 7"), send each named thread my exact words.

Notes for another effort go to that effort's manager as one message with a brief, or into a backlog item with that effort when it has no manager. A task files them as backlog items with that effort, and its manager passes on, from the task's final report, the ones that change that effort's current work. For example, a library task that finds a spec ambiguity adds a spec item, and its manager tells the spec effort's manager.

In replies to me, the desk and managers use two verbs for a thread: Start (launch it, or resume it after a pause) and Pause (park and settle it). Don't say settle, unsettle, park or resume to me.

## Compacting

Settle a compacted thread only when sweep step 5 allows it, also when T3 had settled it on its own before. Before settling a thread, make sure what it needs later is in files or commits, then send `/compact`, wait for it with `t3_thread_wait`, and only then settle it. A queued message cancels a pending settle, so the order matters. Skip compacting threads with fewer than about 40 turn items, and threads whose latest run ended over 60 minutes ago, but still settle them when sweep step 5 allows it. `/compact` works on Claude and Codex threads. OpenCode threads show no result for it, so don't compact them.

A thread's prompt cache expires about an hour after its last turn. Compacting before then is cheap, and a compacted thread is cheap to pick up again later, so the desk compacts idle threads at about 50 minutes, whether or not they wait on me. The listener runs `bin/compact-due` every minute, which prints an `idle` event once per run for each thread with a backlog item that is idle 50 minutes to 3 hours and isn't snoozed, settled or waiting on a request. Under `compact` it lists Claude and Codex threads with 40 or more turn items whose cache is still warm, and under `settle` the rest. Under `archive` it lists, once, each thread without a backlog item that has been settled for 7 days, other than the desk, managers, subagents and snoozed threads. It records each run it reported in `state/compacted.json`. For each thread under `compact`, send `/compact`, wait for it, and record the compaction's run id in `compacted.json`. Then settle each listed thread that sweep step 5 allows, after compacting when that step asks for it. Also record the run id of every compaction you send before settling or pausing a thread, so it isn't compacted again. When settling a thread whose latest run is a recorded compaction, don't compact it again. Wherever a rule looks at a thread's last reply, it means the last reply before any compaction.

The desk and managers compact themselves. When more than about 20 of your turns came since this conversation started or was last compacted, and what you need later is in files, end the turn by queueing `/compact` to yourself with `t3_thread_send` and `mode` `queue` (your id comes from `t3_thread_configuration`). It runs once the turn ends. The desk does this after the listener check.

## Backlog items

`backlog/<id>.json`, where `<id>` is `<yyyymmdd>-<slug>`. Add items with `bin/backlog add` and list them with `bin/backlog list`:

```json
{
  "id": "20261021-keep-volume-after-reconnect",
  "title": "Keep volume after reconnect",
  "repo": "app",
  "effort": "player-sync",
  "kind": "bugfix",
  "label": "user-visible bug",
  "summary": "One or two sentences.",
  "brief": "Evidence and plan, or empty until triaged.",
  "source": "<thread id or 'me'>",
  "created": "2026-10-21",
  "status": "open",
  "thread": null,
  "pr": null,
  "done": null,
  "comments": [],
  "rank": 3,
  "blockedBy": ["20261020-other-item", "library 4.2 released"],
  "suggested": "One line on why I should do this soon."
}
```

`kind` is bugfix, feature, review, design, test or docs. `label` is user-visible bug, reachable but rare or theoretical. `status` is new (my unsorted capture from the board), open, next (my priority list, ordered by `rank`), requested (I pressed Start on the board), started, done (its PR merged, or I marked it done) or dropped. `blockedBy` lists item ids or notes on what it waits for, and `suggested` marks a desk pick. The last three are optional. Set `blockedBy` only when none of the item can move. Note a part that waits in a comment, and don't block a started item that waits on reviewers, since its settled thread shows that. `pr` is the PR URL, `done` the date it finished or was dropped, and `archived` the date I cleared it from the board's Done column. `asks` holds the question its thread waits on me for (`text` and `at`), which the thread sets and clears with `bin/backlog ask`, and the desk sets or clears when the thread didn't. Task threads create items with status open, except that `/desk` adopts the thread's own item and may pause, finish or drop it. Managers change the rest. The desk and managers change an item's status only with `bin/backlog status <id> <open|next|started|done|dropped> [--thread <id>] [--pr <url>] --by <desk|manager>`, never by editing the JSON, so the change reaches `state/events.jsonl`. `next` puts it last in Next. The listener ignores the desk's own changes.

## Effort status files

`efforts/<effort>/status.md` sections, in this order: Resume here, Tasks (table: thread, repo, branch, PR, state, blocked by), Defaults (model and repos), Open decisions, Log (dated, newest last).

## Board

`bin/board` serves the board at http://127.0.0.1:8765. It shows the backlog, a Done view, and the threads from `state/threads.json`, which `bin/board-threads` writes in each sweep and refresh. It leaves out threads whose item is done or dropped, and those whose item is paused unless they run or wait on me, since their cards show them. It keeps the desk's earlier `needsYou` whys while the thread waits, and adds `item` and `effort` to each entry:

```json
{
  "updated": "2026-10-21 09:00",
  "environment": "<environmentId from t3_environment_read>",
  "managers": {"<effort>": "<manager thread id>"},
  "needsYou": [{"thread": "<id>", "title": "...", "why": "push OK for #12", "pr": "<url or null>"}],
  "waiting": [],
  "snoozed": [{"thread": "<id>", "title": "...", "until": "2026-10-23 09:00", "pr": "<url or null>"}],
  "working": [],
  "unassigned": []
}
```

A snoozed thread goes only in `snoozed`, with its wake time in local time. The board puts a started item without `asks` whose thread is in `waiting` in the In review column, and an open item with an open blocker in Blocked. The board adds items with `asks` to Needs you itself and drops a `needsYou` entry for the same thread in their favor.

On the board I can capture notes (status `new`), comment on items, order my Next column, start, pause, finish (Done), drop or reopen items, archive a lane's Done cards, set blockers, and change their effort or repo. The server logs each action to `state/events.jsonl` for `bin/desk-wait`. It never launches anything itself.
