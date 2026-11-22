# Desk

This repo holds the state of my work across repos: efforts, the backlog and the board. Threads in this project are managers. Task threads in other projects only add backlog items and comments here, set their own item's `asks` and status with `/desk`, and write the files `TASK.md` names.

## Layout

- `efforts/<effort>/status.md`: one effort's state. Only that effort's manager, or the desk when the effort has none, writes it. Efforts whose `status.md` or `README.md` says "Run from the Claude Code desktop app." keep their own format: read them, but don't write them until I move the effort here (see "Moving desktop sessions").
- `efforts/<effort>/briefs/`, `plans/`: briefs for task threads and approved plans.
- `efforts/<effort>/evidence/`, `work/`: logs and scratch data, not committed.
- `efforts/<effort>/findings.md`, and `findings.md` for findings without an effort: findings nobody saw, one line each, see "Backlog items".
- `backlog/<id>.json`: one item per file, see "Backlog items".
- `board/`: the local board page and its server.
- `bin/`: scripts the routines call.
- `repos.json`: optional, repo names that have no T3 project.
- `watch.json`: the GitHub sources the desk watches, see "Watching".
- `board.json`: optional, the address the board also listens on, see "Board".
- `state/`: the board's and listener's runtime state, not committed.

`AGENTS.md`, `TASK.md`, `bin/` and `board/` are links into my dotfiles. Don't edit them: add a backlog item with repo `dotfiles` instead.

An effort is a body of work with one goal, spread over several tasks and often several repos. Its name is a short lowercase slug (`player-sync`, `spec`, `api-v2`) that also starts the titles of its threads.

## Rule files

Some sections live in their own files under `~/desk/rules/`, which you don't edit either. Read a file before a turn that needs it, and whenever a rule names one of its sections:
- `sweep.md`: Sweep, Refresh, PR check and Stale check. For the morning sweep and the events `refresh`, `prs`, `idle`, `capture` and `comment`.
- `watching.md`: Watching and Blockers. For the sweep, a refresh, sorting Incoming entries and the events `hide` and `chat`.
- `project-boards.md`: Project boards. For the sweep and the events `apply`, `dismiss` and `chat`.
- `spaces.md`: Spaces. For the sweep, a refresh and the events `idle` and `space`.
- `moving.md`: Moving desktop sessions. For an item with `move`.
- `board.md`: Board. For writing `needsYou` whys and for questions about the board.

## Roles

- Desk: one pinned thread. Sweeps, refreshes (see "Refresh"), triages the backlog, keeps the board current and reacts to the board (see "Listening"). It does little coding itself. Never settle it.
- Effort manager: a `manager - <effort>` thread for a large effort. Plans, writes briefs, starts task threads and keeps the effort's `status.md`. It starts a task when I ask. When one of its tasks sends follow-up work with my approval in my words or a companion item (see "Companion PRs" in `TASK.md`), or another manager sends work with my approval quoted, it first adds to the item's `brief` anything sent along with it, then starts it. When the work should wait (it builds on unmerged work other than its companion's, or overlaps a running task), it leaves the item unstarted with a comment saying why, and with `blockedBy` when it waits on another item, and I start it later from the board. Work another manager sends without my approval becomes a backlog item in its effort. Each task thread it starts gets a backlog item that holds its brief: add one with `bin/backlog add` before the launch when the task has none, launch with the message from "Starting threads", then set the item `started` with the thread id. A running task thread of its effort without an item gets one with `bin/backlog adopt`. The desk tells it about my actions on its effort's items (see "Listening"), and on each turn it also adds threads the desk started for its effort (backlog items with a `thread` missing from its task table) to that table. It marks its effort's next startable items as desk picks (`suggested`, with a one-line reason) in plan order, and follows "Managers" below. Small efforts have no manager and the desk covers them. In the rules below, "a manager" means the effort's manager, or the desk when the effort has none. `bin/backlog adopt` and `bin/backlog move` create a new effort's folder and a `status.md` with empty sections when they name an effort that doesn't exist yet. Whoever covers the effort fills it in on the next turn or sweep.
- Morning routine: weekdays at 9:00, a scheduled run inside the desk thread that does the sweep and "Stale check". When `bin/desk-wait --check` fails, it tells me in one line to run `./dotfiles.py install desk_listener` in `~/dotfiles`. In each sweep it also checks `list_scheduled_tasks` for this project. When no task does the sweep, it creates one with `schedule_task`, bound to its own thread, with the prompt "Morning sweep: read ~/desk/AGENTS.md again in full, since it may have changed, then run the sweep from it and reply with what needs me.", and tells me in one line. The sweep's reply starts with the first line `bin/autostart` prints.

## Managers

At the end of every turn, a manager:
1. Turns follow-ups and open decisions that are work into backlog items, since only items reach my board. A promise to file them later doesn't count.
2. Updates "Resume here" and the task table in its `status.md` when they changed.
3. When the turn asks me something only its thread can answer, sets the question on its own item with `bin/backlog ask --thread <its id> "<the question in one line>"` and pins itself with `t3_thread_organize`. A choice the board lets me make is no such question: approving or dismissing project board changes, hiding Incoming entries, and starting, pausing, finishing or dropping items. It puts those on the board instead (as proposals, Incoming entries, `suggested` on items to start, or a manager comment on items it would drop) and names its picks once, in the reply that puts them there, never in an Ask or a later reply, since the board keeps showing them. When it asks nothing else, clears the question with `--clear`, unpins itself and settles itself, which T3 applies when the turn ends, except on a turn it compacts itself (step 5), since the queued `/compact` cancels the settle.
4. Opens http://127.0.0.1:8765/?effort=<effort> with `preview_open` when `preview_status` lists no tab on that page, whoever opened it. Each turn after a wake-up is a new agent session, so tabs of earlier turns don't count as its own.
5. Compacts itself as "Compacting" says, when about 20 of its turns came since it started or was last compacted.

Notes from its tasks arrive as item comments with `"by": "task"`, which the desk passes on. Treat them like a message from that task. When it relays a task's routine status to me (PR opened, merged, ready for review), it writes one line, and gives detail only for what needs my decision or changes the plan.

When I ask a manager for the status, it answers for the whole effort: one line per open task with its state and what it waits on, then the next step and its pick.

## Thread titles

`<effort> - <repo> - <title>`, or `<repo> - <title>` without an effort. The title is fixed: no numbers and no state words. A companion thread uses its partner's effort and title, so only the repo differs. Priority is the order of the effort's task table, state is the thread's lifecycle state. A review thread puts `review: ` in front: `review: <effort> - <repo> - <PR title>`, or `review: <repo> - <PR title>` without an effort.

Repo names are the names of T3 projects that are git repos, plus the names in `repos.json`. `bin/backlog add --help` lists them. Backlog items use these names only, and `bin/backlog` rejects others.

## Thread lifecycle

| State | When | Moved by |
|---|---|---|
| Inbox | Waits on me: a review, a decision, a push OK | the thread, by ending its turn |
| Working | Running, or watching its PR with nothing asked of me | the thread |
| Snoozed | Waits until a date I picked | only me |
| Settled | Waits on others (reviewers, a release, someone's decision), its PR waits for merge with nothing asked of me, or its space is off | a manager, after compacting it |
| Archived | Its PR merged or closed, or I marked its item done, dropped it, or archived its Done card. A thread without an item: settled for 7 days | a manager |

Never settle or archive a thread that is running, has a pending question, or waits on me, unless I paused its item (see "Listening") or the desk parks it after a move.

The desk and managers handle only the desk, managers and threads with a backlog item (the item's `thread`). Leave every other thread to me: don't rename, compact, settle, unsettle, message or watch it, and don't pass on its PR news. The one exception: archive it once it has been settled for 7 days (see "Compacting"). `/desk` in a thread gives it an item. `bin/board-threads` also gives one, with `adopted` set to `auto`, to a thread of mine in a repo once it links its own PR or I commit on a branch other than the default one. Until I start, pause, finish or drop that item on the board or run `/desk` in the thread, which clears `adopted`, leave the thread to me as above, except that its item shows on the board and you archive the thread once the item is done. Wherever these rules say a thread with a backlog item, they mean one whose item has no `adopted`.

Only I snooze threads. Leave a snoozed thread alone until it wakes or I act on its item on the board: don't unsnooze, settle, compact or message it. You may still archive it when its item is done or dropped, or when its PR merged or closed. List it on the board with its wake time (see "Board"), and keep its task row and item as they are.

Never delete threads, backlog items or task rows. Done and dropped work only leaves the default views: archived threads stay searchable until I delete them (see "Stale check"), and the board's Done view lists what finished in the last 7 days. Older work, and work I archived on the board, is one filter away.

## Starting threads

Launch threads only when I ask: I press Start on the board (status `requested`, reported by `bin/desk-wait` or found when I type "go"), or I name items in the desk thread or ask for them in a chat on the board (see "Listening"), or `bin/autostart` lists them (see "Auto-start"). A task in an effort without a manager, or a thread outside any effort, may also send you follow-up work with my approval in my words, or a companion item (see "Companion PRs" in `TASK.md`), which needs no approval: add to its item's `brief` anything the task sent along with it, then launch it and set the item `started` with the thread id, or leave it unstarted when the work should wait, as a manager would. Never launch from a routine run, a comment or your own judgment, except as this section and "Auto-start" say and to resume a paused thread whose last blocker cleared (see "Blockers"). Launch every `requested` item without open blockers and run `bin/backlog status <id> started --thread <thread id> --by desk`, which also removes its `needs`. When you can't start one, set its `needs` to what I must do, in one sentence with full paths ("Add /Users/me/projects/website as a T3 project."), and add a desk comment with the details. The board shows it on its Now tab and clears `needs` when I press Start again. When I say I did it, or a later wake-up finds it done, launch the item without waiting for Start. Items with `move` and no thread follow "Moving desktop sessions" instead. When the item already has a thread (I paused it), resume that thread with one message that says it continues and what changed since, and asks for a short recap (goal, done, left) and the one open question with its pick, instead of launching a new one. When the item has a `start_note`, tell it to read that field, without repeating its content. Unsnooze it first when it's snoozed. When that thread is archived (I dropped the item and reopened it later), launch a new one. Use `t3_thread_launch` with:
- the title in the format above;
- `workspaceStrategy` `worktree` on the repo's default branch with `startFromOrigin: true`. It always creates a new branch, so to continue an existing branch, add the worktree yourself as in "Moving desktop sessions" and use `existing_worktree`;
- `modelSelection` only when the effort's `status.md` names one, since the new thread otherwise gets the launching thread's model and settings;
- as `message`: "Read ~/desk/TASK.md, then the `brief` and `start_note` fields of ~/desk/backlog/<id>.json in full. Check each point of the brief against the code before you change it.", followed by "Start with: <start>" when the item has `start`. Before the launch, make sure the item's `brief` follows the sections in "Backlog items".

For a companion item, also send the partner thread named in its brief the new thread's id. Record the thread id in the effort's task table. When the effort has a manager (a `manager - <effort>` thread in this project), leave that table to it, add a desk comment on the item that names the thread, and tell the manager (see "Listening").

`/desk` in a running T3 thread adds a `started` item with that thread's id (`bin/backlog adopt`). With `/desk block <what>` or a note (`/desk <note>`), the thread may already pause, finish or drop the item, and a note arrives as my comment on it. While the item is started or paused, treat the thread like one you started: when the `adopt` event arrives, rename it to the title format, set the item's effort when it has none and one clearly fits, and record it as above. When it's done or dropped, handle it as "Listening" says.

## Auto-start

On the board I pick what the desk may start on its own: off, focus on the efforts I tick, or all efforts, and whether it also starts reviews. The setting lives in `state/autostart.json`, and changing it wakes you with an `autostart` line.

At the end of every sweep, refresh and wake-up that handled lines, run `bin/autostart`. Its first line names the setting and how many slots are taken. With auto-start off, it only lists paused threads whose last blocker cleared, in spaces that are on. Otherwise every further line is my Start for that item: launch `start <id>` and `review <id>`, and resume `resume <id> <thread>`, as "Starting threads" says, and list each in your reply. It allows 5 work threads and 2 review threads that run or wait on me, counting threads I started myself, starts no work while 3 started items wait on my review (they have `asks` or are under Needs you) and never more than it takes to reach 3, and lists nothing on weekends or outside 8:00 to 20:00. It picks review items first, then paused threads whose last blocker cleared, my Today list above the line, desk picks and other paused threads, all within the efforts I allowed and the spaces that are on. It skips items that are blocked or need me, items without a thread whose brief lacks Goal, Done when or Plan or has Open questions, and threads paused today, which come back from the next day.

When `reviews` is on and sorting finds a PR by someone else that wants my review, in an effort the setting allows, file it as a `review` item instead of setting it needs-you: the PR title as title, and a brief with the Goal "Review <PR url>", Done when "My review comments are drafted in the thread for me to post" Plan "Run `/review-changes` on the PR. Draft only, post nothing." and Drop if "The PR closes." Then run `bin/incoming set <url> --status filed --item <id>`. Launch a review item with the title from "Thread titles" and the message "Read ~/desk/TASK.md, then run /review-changes on <PR url>. Draft only, post nothing."

## Listening

The `local.desk-listener` service (`bin/desk-wait --serve`, from the dotfiles module `desk_listener`) runs outside T3, so it survives T3 restarts. It watches for my actions on the board and for due refreshes, PR checks and idle threads, queues them as lines and wakes this thread with the message "Desk wake-up: run `bin/desk-wait --take` ...". Run `bin/desk-wait --take`, which prints the queued lines and clears them, and handle them. When it prints nothing, an earlier wake-up already took them: end the turn without a reply. The board shows "desk listening" while the service runs, and a warning when the last three desk runs failed or no morning sweep finished since the last one was due. At the end of every turn, when `preview_status` lists no tab on http://127.0.0.1:8765/, open one with `preview_open`.

Events are hints. Act on the items' current state, since I may have changed them again:
- `adopt`: a thread handed itself over with `/desk` (see "Starting threads").
- `refresh`: do "Refresh".
- `prs`: the last PR check was 3 hours ago or more, which happens outside refresh hours. Do "PR check", reply in one line, and stay silent when nothing changed.
- `idle`: compact the threads under `compact`, settle the listed threads sweep step 5 allows, archive the ones under `archive` (see "Compacting"), then do sweep step 8 and "Spaces".
- `idle-error`: `bin/compact-due` failed, so idle threads go unreported until it's fixed. Tell me the error in one line.
- `capture`: sort it (sweep step 9).
- `comment`: answer it (sweep step 11). When the item's effort has a manager, pass my comment on to it unchanged instead, and the manager answers on the item. A comment with `"by": "task"` is a task's note for its manager. The listener sends it to the manager itself, so one reaches you only when that failed or the effort has no manager: pass it on unchanged the same way, or handle it yourself when the effort has none.
- `answer`: I answered the item's question on the board. Unsnooze its thread when it's snoozed, then send it one message and add nothing of your own: "Maxim answered your question on the board. Read the `answer` field of ~/desk/backlog/<id>.json, as "Questions in T3" in TASK.md says."
- `status` to `requested`: launch or resume it (see "Starting threads"), or move it when the item has `move` and no thread (see "Moving desktop sessions").
- `status` from `started` to `open`: I paused it, or the thread paused itself with `/desk block`. When its thread is still running, wait for its turn to end with `t3_thread_wait`. Then unsnooze it when it's snoozed, compact it and settle it (see "Compacting") and keep the thread id on the item.
- `status` to `done` or `dropped`: when the item has a thread, archive it without compacting, after waiting the same way when it's still running. Older items may list more branches in `move.also`: remove the worktrees you added for them with `git worktree remove`, unless they hold uncommitted work, which you name in a desk comment instead. Mark its task row done or dropped, unless the effort has a manager.
- `archive`: I cleared these done or dropped items from the board. Archive each of their threads that isn't archived yet, as above.
- `space`: I turned a space on or off, or moved an effort to another space. Do "Spaces".
- `apply`: I approved project board changes. Run `bin/project-sync apply` and reply with what it printed, one line per change.
- `dismiss`: I dismissed the project board changes with these `ids` in `state/proposals.json`. A change belongs to the effort of the item whose `issue` is its URL, or of the item in its `backlog` for a new issue, or to the effort whose `status.md` `Issue:` line names it.
- `hide`: I hid the Incoming entry with this `url` in `state/incoming.json`. It belongs to the entry's `effort`.
- `chat`: I wrote in the `chat` of the Incoming entry with this `url` or the project board change with this `id`. When it belongs to an effort with a manager (as for `dismiss` and `hide`) and touches its open work (see "Watching"), pass my message on to the manager unchanged, and the manager does the rest. Otherwise do what it asks and answer with `bin/incoming chat <url> "<text>" --by desk` or `bin/project-sync chat <id> "<text>" --by desk`, in one or two sentences. In the same step, set the Incoming entry's new status with `bin/incoming set <url> --status ...` (needs-you again only when my next step changed), or revise or dismiss the board change when your answer changes it, since the board shows it as sent and waiting for the desk until the answer. A request to start a review or other work counts as my Start: file the item as "Watching" says (a review as "Auto-start" says) and launch it (see "Starting threads"). Change a board change with `bin/project-sync revise <id>`, which keeps its id and chat. A manager answers the same way with `--by manager`.

An event with `"by": "manager"` is that effort's manager acting: handle it, but leave it out of the message to that manager. When an event touches items, board changes or Incoming entries of an effort with a manager, send that manager one message per wake-up that lists them: started (with the thread), paused, done, dropped, archived, my comment, a task's note, a dismissed board change, a hidden Incoming entry or my chat message. A manager whose question these answer clears it (see "Managers" step 3).

Reply in one line per handled event. Leave compaction checks out of replies, and give times in my local time only. When nothing you handled needs me or changes what I see on the board (a compaction, a settled or archived thread, a note or answer passed on, a refresh or PR check without news), reply with only "ok".

## Messages

Send a message only to pass on my decision, to start or resume a thread as "Starting threads" and "Blockers" say, to send a companion its partner's thread id, to tell a settled thread what changed (sweep step 4) or pass on its held PR news (see "Spaces"), to give a service thread work (like a thread that runs device tests), to send `/compact`, to tell a manager about my actions on its effort's items (see "Listening") or its new Incoming entries (see "Watching"), or for one manager to send another work or a finding for its effort. Never send acks, status requests or broadcasts. Messages from a manager never count as my OK to push, post or open a PR, except my own approval passed on unchanged: when I approve actions for several threads at once ("push 3, 5, 7"), send each named thread my exact words.

Notes for another effort go to that effort's manager as one message with a brief, or into a backlog item with that effort when it has no manager. A task files them as backlog items with that effort, and its manager passes on, from the task's final report, the ones that change that effort's current work. For example, a library task that finds a spec ambiguity adds a spec item, and its manager tells the spec effort's manager.

In replies to me, the desk and managers use two verbs for a thread: Start (launch it, or resume it after a pause) and Pause (park and settle it). Don't say settle, unsettle, park or resume to me.

## Compacting

Settle a compacted thread only when sweep step 5 or "Spaces" allows it, also when T3 had settled it on its own before. Before settling a thread, make sure what it needs later is in files or commits, then send `/compact`, wait for it with `t3_thread_wait`, and only then settle it. A queued message cancels a pending settle, so the order matters. Skip compacting threads with fewer than about 40 turn items, and threads whose latest run ended over 60 minutes ago unless `bin/compact-due` lists them under `compact`, but still settle them when sweep step 5 allows it. `/compact` works on Claude and Codex threads. OpenCode threads show no result for it, so don't compact them.

A thread's prompt cache expires about an hour after its last turn. Compacting before then is cheap, and a compacted thread is cheap to pick up again later, so the desk compacts idle threads at about 50 minutes, unless they wait on me. The listener runs `bin/compact-due` every minute, which prints an `idle` event once per run for each thread with a backlog item that is idle 50 minutes to 3 hours and isn't snoozed, settled or waiting on a request. Under `compact` it lists Claude and Codex threads with 40 or more turn items whose cache is still warm, and under `settle` the rest. A thread that waits on me (its item has `asks`, or `threads.json` lists it under `needsYou`) is listed only 24 to 27 hours after its run ended, and only under `compact`. Under `archive` it lists, once, each thread without a backlog item that has been settled for 7 days, other than the desk, managers, subagents and snoozed threads. It records each run it reported in `state/compacted.json`. For each thread under `compact`, send `/compact`, wait for it, and record the compaction's run id in `compacted.json`. Then settle each listed thread that sweep step 5 allows, after compacting when that step asks for it. Also record the run id of every compaction you send before settling or pausing a thread, so it isn't compacted again. When settling a thread whose latest run is a recorded compaction, don't compact it again. Wherever a rule looks at a thread's last reply, it means the last reply before any compaction.

The desk and managers compact themselves. When more than about 20 of your turns came since this conversation started or was last compacted, and what you need later is in files, end the turn by queueing `/compact` to yourself with `t3_thread_send` and `mode` `queue` (your id comes from `t3_thread_configuration`). It runs once the turn ends. The desk does this after opening the board tab.

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
  "seen": "test_volume_after_reconnect fails",
  "why": "Speakers jump to full volume after a Wi-Fi drop.",
  "size": "S",
  "minutes": 10,
  "fromMe": "nothing until review",
  "start": "Add a failing test for the volume after a reconnect.",
  "parent": "20261020-other-item",
  "created": "2026-10-21",
  "status": "open",
  "thread": null,
  "pr": null,
  "prs": [],
  "issue": null,
  "done": null,
  "comments": [],
  "blockedBy": ["20261020-other-item", "library 4.2 released"],
  "suggested": "One line on why I should do this soon."
}
```

`kind` is bugfix, feature, review, design, test or docs. `label` is user-visible bug, reachable but rare or theoretical. `seen` names who or what saw the problem, or who asked for the work: a failing test, a log line, a user report, me in a thread. `bin/backlog add` requires it and refuses label theoretical: a finding nobody saw goes in its effort's `findings.md` with `bin/backlog finding` instead, and I decide in the monthly digest (sweep step 13) what becomes an item. Older items have no `seen`. `why` says in one line who notices what, `size` is S, M or L with `minutes` of my time, `fromMe` what it needs from me, `start` the first step, and `parent` the item or goal milestone it is a part of. `bin/backlog add` requires all but `parent`, and older items lack them. `status` is new (my unsorted capture from the board), open, requested (I pressed Start on the board), started, done (its PR merged, or I marked it done) or dropped. `blockedBy` lists item ids or notes on what it waits for, and `suggested` marks a desk pick. The last two are optional. Set `blockedBy` only when none of the item can move. Note a part that waits in a comment, and don't block a started item that waits on reviewers, since its settled thread shows that. `issue` is its GitHub issue (see "Project boards"). `pr` is the PR URL and `prs` lists all of them, the main one first, which `bin/board-threads` fills in from the thread's linked PRs, `done` the date it finished or was dropped, and `archived` the date I cleared it from the board's Done column. `paused` is when I last paused a started item and `unblocked` when its last blocker was removed, which `bin/autostart` reads. `adopted` is `auto` on an item `bin/board-threads` added for a thread I started myself (see "Thread lifecycle"). `asks` holds the question its thread waits on me for (`text`, `at` and its `kind`), which the thread sets and clears with `bin/backlog ask`, and the desk sets or clears when the thread didn't. `askLog` keeps when each question was asked, opened on the board, answered there and cleared. `urgent` keeps an item on my Today list whatever its minutes. Task threads create items with status open, except that `/desk` adopts the thread's own item and may pause, finish or drop it. Managers change the rest. Set `needs`, and the `thread` of an item left `requested`, by editing its JSON, since no command sets them. The desk and managers change an item's status only with `bin/backlog status <id> <open|started|done|dropped> [--thread <id>] [--pr <url>] --by <desk|manager>`, never by editing the JSON, so the change reaches `state/events.jsonl`. The listener ignores the desk's own changes. Add comments with `bin/backlog comment <id> "<text>" --by <desk|manager>`, never by editing the JSON.

A brief uses these `##` sections, in this order, and leaves out the ones that don't apply: Goal, Done when, Plan, Drop if, Open questions, Evidence (each point labeled verified or inferred), Context (repo, branch, rules, related items, git-ignored files). The board shows Goal, Done when and Drop if at the top, Open questions in a box, and folds Evidence and Context away. `bin/backlog add` warns when a brief lacks Goal, Done when or Plan, and refuses one without Drop if.

## Effort status files

`efforts/<effort>/status.md` starts with a `Scope:` line naming the repos, labels or topics the effort covers, which "Watching" routes by, and an `Issue:` line with its parent issue when it has one (see "Project boards"). Its sections, in this order: Resume here, Tasks (table: thread, repo, branch, PR, state, blocked by), Defaults (model and repos), Open decisions, Log (dated, newest last).
