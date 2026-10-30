# Desk

This repo holds the state of my work across repos: efforts, the backlog and the board. Threads in this project are managers. Task threads in other projects only add backlog items and comments here, set their own item's `asks` and status with `/desk`, and write the files `TASK.md` names.

## Layout

- `efforts/<effort>/status.md`: one effort's state. Only that effort's manager, or the desk when the effort has none, writes it. Efforts whose `status.md` or `README.md` says "Run from the Claude Code desktop app." keep their own format: read them, but don't write them until I move the effort here (see "Moving desktop sessions").
- `efforts/<effort>/briefs/`, `plans/`: briefs for task threads and approved plans.
- `efforts/<effort>/evidence/`, `work/`: logs and scratch data, not committed.
- `backlog/<id>.json`: one item per file, see "Backlog items".
- `board/`: the local board page and its server.
- `bin/`: scripts the routines call.
- `repos.json`: optional, repo names that have no T3 project.
- `watch.json`: the GitHub sources the desk watches, see "Watching".
- `state/`: the board's and listener's runtime state, not committed.

`AGENTS.md`, `TASK.md`, `bin/` and `board/` are links into my dotfiles. Don't edit them: add a backlog item with repo `dotfiles` instead.

An effort is a body of work with one goal, spread over several tasks and often several repos. Its name is a short lowercase slug (`player-sync`, `spec`, `api-v2`) that also starts the titles of its threads.

## Roles

- Desk: one pinned thread. Sweeps, refreshes (see "Refresh"), triages the backlog, keeps the board current and reacts to the board (see "Listening"). It does little coding itself. Never settle it.
- Effort manager: a `manager - <effort>` thread for a large effort. Plans, writes briefs, starts task threads and keeps the effort's `status.md`. It starts a task when I ask. When one of its tasks sends follow-up work with my approval in my words or a companion item (see "Companion PRs" in `TASK.md`), or another manager sends work with my approval quoted, it first adds to the item's `brief` anything sent along with it, then starts it. When the work should wait (it builds on unmerged work other than its companion's, or overlaps a running task), it leaves the item unstarted with a comment saying why, and with `blockedBy` when it waits on another item, and I start it later from the board. Work another manager sends without my approval becomes a backlog item in its effort. Each task thread it starts gets a backlog item that holds its brief: add one with `bin/backlog add` before the launch when the task has none, launch with the message from "Starting threads", then set the item `started` with the thread id. A running task thread of its effort without an item gets one with `bin/backlog adopt`. The desk tells it about my actions on its effort's items (see "Listening"), and on each turn it also adds threads the desk started for its effort (backlog items with a `thread` missing from its task table) to that table. It marks its effort's next startable items as desk picks (`suggested`, with a one-line reason) in plan order, and follows "Managers" below. Small efforts have no manager and the desk covers them. In the rules below, "a manager" means the effort's manager, or the desk when the effort has none. `bin/backlog adopt` and `bin/backlog move` create a new effort's folder and a `status.md` with empty sections when they name an effort that doesn't exist yet. Whoever covers the effort fills it in on the next turn or sweep.
- Morning routine: weekdays at 9:00, a scheduled run inside the desk thread that does the sweep, and on Thursdays also "Stale check". When `bin/desk-wait --check` fails, it tells me in one line to run `./dotfiles.py install desk_listener` in `~/dotfiles`. In each sweep it also checks `list_scheduled_tasks` for this project. When no task does the sweep, it creates one with `schedule_task`, bound to its own thread, with the prompt "Morning sweep: read ~/desk/AGENTS.md again in full, since it may have changed, then run the sweep from it and reply with what needs me.", and tells me in one line.

## Managers

At the end of every turn, a manager:
1. Turns follow-ups and open decisions that are work into backlog items, since only items reach my board. A promise to file them later doesn't count.
2. Updates "Resume here" and the task table in its `status.md` when they changed.
3. When the turn asks me something, sets the question on its own item with `bin/backlog ask --thread <its id> "<the question in one line>"` and pins itself with `t3_thread_organize`. When it asks nothing, clears the question with `--clear`, unpins itself and settles itself, which T3 applies when the turn ends, except on a turn it compacts itself (step 5), since the queued `/compact` cancels the settle.
4. Opens http://127.0.0.1:8765/?effort=<effort> with `preview_open` when `preview_status` lists no tab on that page, whoever opened it. Each turn after a wake-up is a new agent session, so tabs of earlier turns don't count as its own.
5. Compacts itself as "Compacting" says, when about 20 of its turns came since it started or was last compacted.

Notes from its tasks arrive as item comments with `"by": "task"`, which the desk passes on. Treat them like a message from that task.

When I ask a manager for the status, it answers for the whole effort: one line per open task with its state and what it waits on, then the next step and its pick.

## Thread titles

`<effort> - <repo> - <title>`, or `<repo> - <title>` without an effort. The title is fixed: no numbers and no state words. A companion thread uses its partner's effort and title, so only the repo differs. Priority is the order of the effort's task table, state is the thread's lifecycle state.

Repo names are the names of T3 projects that are git repos, plus the names in `repos.json`. `bin/backlog add --help` lists them. Backlog items use these names only, and `bin/backlog` rejects others.

## Thread lifecycle

| State | When | Moved by |
|---|---|---|
| Inbox | Waits on me: a review, a decision, a push OK | the thread, by ending its turn |
| Working | Running, or watching its PR with nothing asked of me | the thread |
| Snoozed | Waits until a date I picked | only me |
| Settled | Waits on others (reviewers, a release, someone's decision), or its PR waits for merge with nothing asked of me | a manager, after compacting it |
| Archived | Its PR merged or closed, or I marked its item done, dropped it, or archived its Done card. A thread without an item: settled for 7 days | a manager |

Never settle or archive a thread that is running, has a pending question, or waits on me, unless I paused its item (see "Listening") or the desk parks it after a move.

The desk and managers handle only the desk, managers and threads with a backlog item (the item's `thread`). Leave every other thread to me: don't rename, compact, settle, unsettle, message or watch it, and don't pass on its PR news. The one exception: archive it once it has been settled for 7 days (see "Compacting"). `/desk` in a thread gives it an item.

Only I snooze threads. Leave a snoozed thread alone until it wakes or I act on its item on the board: don't unsnooze, settle, compact or message it. You may still archive it when its item is done or dropped, or when its PR merged or closed. List it on the board with its wake time (see "Board"), and keep its task row and item as they are.

Never delete threads, backlog items or task rows. Done and dropped work only leaves the default views: archived threads stay searchable, and the board's Done view lists what finished in the last 7 days. Older work, and work I archived on the board, is one filter away.

## Sweep

1. List threads in all projects, settled and snoozed ones included, with their linked PRs.
2. Leave threads without a backlog item alone (see "Thread lifecycle"). The board lists them, as unassigned when their title names no effort.
3. Read every linked PR of a thread with a backlog item with `gh`: state, checks, mergeable, and reviews or comments by people other than me and bots.
4. Do "PR check".
5. Compact, then settle, each thread with a backlog item that isn't snoozed, has been idle for 50 minutes or more, and waits only on others: it has an open PR or its last reply says what it waits on, no reply since my last message asks me something or says the work is finished (step 7 handles those), its item has no `asks`, and no review round is running (see "Compacting"). The 50 minutes keep a thread I'm working with between messages. Settling ends a thread's T3 PR watch, so later news reaches it through step 4. A thread that watches with `bin/pr-check --wait` may hear the same news twice, which it handles once. When a thread with a backlog item that isn't running, snoozed or settled has linked PRs and a reply since my last message asks me something or its item has `asks`, however long it has been idle, call `unwatch_pull_request` with its thread id for each of them, since a watched thread stays in my Working list instead of my inbox. Settle a thread with a PR it doesn't watch only in a full sweep (not a refresh or `idle`), after reading the PR with `gh`. Managers settle themselves (see "Managers"). A manager whose item has no `asks` and that asked me nothing since my last message counts as waiting on others: unpin it and settle it without compacting it, since pinning unsettles a thread.
6. Archive settled and snoozed threads with a backlog item whose PR closed, or merged without step 8 marking the item done, more than a day ago. Mark their task row and backlog item done with the date, the PR and the thread id.
7. Read the thread of every `started` item (`t3_thread_read`). When the thread is archived or gone, mark the item done with today's date and add a desk comment that it was closed outside the desk. When the thread isn't snoozed, is idle and has no PR, and its last reply says the work is finished, list it in `needsYou` with the why "finished? mark it done on the board". When the thread isn't snoozed, a reply since my last message asks me something, and the item has no `asks`, set it with `bin/backlog ask --thread <id> "<the question in one line>"`. When the item has `asks` and I answered in the thread after `asks.at`, with no later reply asking me something, clear it with `bin/backlog ask --thread <id> --clear`. Unsettle a settled thread whose item has `asks`, since a settled thread leaves my inbox. When the thread isn't a manager, is settled, has no open PR, its item has no blocker, and its last reply neither says it waits on someone else nor that the work is finished, I settled it by hand to put it aside: pause the item with `bin/backlog status <id> open --by desk`, which keeps its thread.
8. Run `bin/board-threads`, which rebuilds `state/threads.json` from T3's database and the backlog and prints the entries that changed, then fix any new `needsYou` why that is wrong (see "Board"). It also copies the PRs a thread linked into its item (`+pr` lines), and marks a started item done once all its PRs merged (`done` lines). For each `done` line, archive the item's thread without compacting, after waiting for a running turn as for my `done` events, mark its task row done unless the effort has a manager, and tell that manager as for my own changes (see "Listening"). Read `threads.json` only when you need more than that. When it fails because T3's database changed, call `t3_thread_list` for every project, settled and snoozed included, and pipe the results into `bin/board-threads --stdin`. Then reply with what needs me, in priority order, one line each.
9. Sort my captures (status `new`, my raw notes in `brief`): turn each into one or more proper items, one per idea, with title, kind, label, repo, effort, summary and brief, status `open`, and the original note quoted in a desk comment. When a capture becomes one item, run `bin/backlog reslug <id>` after giving it its title, fix the effort files it lists, and tell a started thread its brief's new path. Keep a repo or effort I picked, unless my note says I'm unsure of it: then check where the code lives and pick that repo, saying why in the comment. When a note is too unclear to sort, leave it `new` and ask in a comment.
10. Triage open backlog items: set the repo name and the effort, drop duplicates and items whose fix is already on the default branch (with a comment saying why), and fill in missing briefs. Set `blockedBy` when none of an item can move before another item or an outside event, and remove blockers that no longer hold, also on started items, as "Blockers" says. A blocker that names a date holds until that date: on it, remove the blocker, add a desk comment and list the item in your reply, and resume its thread as "Blockers" says when it was the last one. Mark up to five open items I should do soon with `suggested` (a one-line reason) and remove it from items that no longer fit. In efforts with a manager, leave `suggested` to the manager. Move items into Next only when my note or message asks for it, and put them last, since that column is my order.
11. Answer new comments on backlog items (`"by": "me"`) with a comment of your own (`"by": "desk"`), and apply what they ask that needs no launch.
12. Do "Watching", then "Project boards".

After a sweep, run `bin/desk-wait --refreshed`, since the sweep covers a refresh.

Base every state on threads, git and `gh`, never on memory, and fix `status.md` where it differs. Take dates and times from `date`, never from memory.

## Refresh

On weekdays from 8:00 to 20:00, the listener queues `refresh` when the last refresh was 45 minutes ago or more. A refresh is a short sweep that keeps the board's thread lists and Incoming current: do sweep steps 1, 2, 4, 5, 7 and 8, read PRs only through `bin/pr-check`, and do "Watching". Reply in one line for the threads, plus one line per entry you set to needs-you, and stay silent when nothing changed.

## Starting threads

Launch threads only when I ask: I press Start on the board (status `requested`, reported by `bin/desk-wait` or found when I type "go"), or I name items in the desk thread. A task in an effort without a manager, or a thread outside any effort, may also send you follow-up work with my approval in my words, or a companion item (see "Companion PRs" in `TASK.md`), which needs no approval: add to its item's `brief` anything the task sent along with it, then launch it and set the item `started` with the thread id, or leave it unstarted when the work should wait, as a manager would. Never launch from a routine run, a comment or your own judgment, except as this section says and to resume a paused thread whose last blocker cleared (see "Blockers"). Launch every `requested` item without open blockers and run `bin/backlog status <id> started --thread <thread id> --by desk`, which also removes its `needs`. When you can't start one, set its `needs` to what I must do, in one sentence with full paths ("Add /Users/me/projects/website as a T3 project."), and add a desk comment with the details. The board shows it under "Needs you" and clears `needs` when I press Start again. When I say I did it, or a later wake-up finds it done, launch the item without waiting for Start. Items with `move` and no thread follow "Moving desktop sessions" instead. When the item already has a thread (I paused it), resume that thread with one message that says it continues and what changed since, and asks for a short recap (goal, done, left) and the one open question with its pick, instead of launching a new one. Unsnooze it first when it's snoozed. When that thread is archived (I dropped the item and reopened it later), launch a new one. Use `t3_thread_launch` with:
- the title in the format above;
- `workspaceStrategy` `worktree` on the repo's default branch with `startFromOrigin: true`. It always creates a new branch, so to continue an existing branch, add the worktree yourself as in "Moving desktop sessions" and use `existing_worktree`;
- `modelSelection` only when the effort's `status.md` names one, since the new thread otherwise gets the launching thread's model and settings;
- as `message`: "Read ~/desk/TASK.md, then the `brief` field of ~/desk/backlog/<id>.json in full. Confirm each point before changing code." Before the launch, make sure the item's `brief` follows the sections in "Backlog items".

For a companion item, also send the partner thread named in its brief the new thread's id. Record the thread id in the effort's task table. When the effort has a manager (a `manager - <effort>` thread in this project), leave that table to it, add a desk comment on the item that names the thread, and tell the manager (see "Listening").

`/desk` in a running T3 thread adds a `started` item with that thread's id (`bin/backlog adopt`). With `/desk block <what>` or a note (`/desk <note>`), the thread may already pause, finish or drop the item, and a note arrives as my comment on it. While the item is started or paused, treat the thread like one you started: when the `adopt` event arrives, rename it to the title format, set the item's effort when it has none and one clearly fits, and record it as above. When it's done or dropped, handle it as "Listening" says.

## Listening

The `local.desk-listener` service (`bin/desk-wait --serve`, from the dotfiles module `desk_listener`) runs outside T3, so it survives T3 restarts. It watches for my actions on the board and for due refreshes, PR checks and idle threads, queues them as lines and wakes this thread with the message "Desk wake-up: run `bin/desk-wait --take` ...". Run `bin/desk-wait --take`, which prints the queued lines and clears them, and handle them. When it prints nothing, an earlier wake-up already took them: end the turn without a reply. The board shows "desk listening" while the service runs. At the end of every turn, when `preview_status` lists no tab on http://127.0.0.1:8765/, open one with `preview_open`.

Events are hints. Act on the items' current state, since I may have changed them again:
- `adopt`: a thread handed itself over with `/desk` (see "Starting threads").
- `refresh`: do "Refresh".
- `prs`: the last PR check was 3 hours ago or more, which happens outside refresh hours. Do "PR check", reply in one line, and stay silent when nothing changed.
- `idle`: compact the threads under `compact`, settle the listed threads sweep step 5 allows, archive the ones under `archive` (see "Compacting"), then do sweep step 8.
- `idle-error`: `bin/compact-due` failed, so idle threads go unreported until it's fixed. Tell me the error in one line.
- `capture`: sort it (sweep step 9).
- `comment`: answer it (sweep step 11). When the item's effort has a manager, pass my comment on to it unchanged instead, and the manager answers on the item. A comment with `"by": "task"` is a task's note for its manager: pass it on unchanged the same way, or handle it yourself when the effort has none.
- `status` to `requested`: launch or resume it (see "Starting threads"), or move it when the item has `move` and no thread (see "Moving desktop sessions").
- `status` from `started` to `open` or `next`: I paused it, or the thread paused itself with `/desk block`. When its thread is still running, wait for its turn to end with `t3_thread_wait`. Then unsnooze it when it's snoozed, compact it and settle it (see "Compacting") and keep the thread id on the item.
- `status` to `done` or `dropped`: when the item has a thread, archive it without compacting, after waiting the same way when it's still running. Older items may list more branches in `move.also`: remove the worktrees you added for them with `git worktree remove`, unless they hold uncommitted work, which you name in a desk comment instead. Mark its task row done or dropped, unless the effort has a manager.
- `archive`: I cleared these done or dropped items from the board. Archive each of their threads that isn't archived yet, as above.
- `apply`: I approved project board changes. Run `bin/project-sync apply` and reply with what it printed, one line per change.

An event with `"by": "manager"` is that effort's manager acting: handle it, but leave it out of the message to that manager. When an event touches items of an effort with a manager, send that manager one message per wake-up that lists them: started (with the thread), paused, done, dropped, archived, my comment, or a task's note.

Reply in one line per handled event. Leave compaction checks out of replies, and give times in my local time only.

## PR check

Settled threads don't watch their PRs, so the desk passes on their PR news.
1. List all projects, and in each the settled threads with linked PRs and a backlog item.
2. Run `bin/pr-check <thread id>=<PR url> ...` once with all of them. It prints news since its last run, and a merge or close on every run: reviews and comments by people other than me and bots, conflicts, failed checks, merges and closes.
3. For each line it prints: a PR merged or closed more than a day ago gets sweep step 6. On any other news, except a merge or close from the last day, unsettle the thread (never a snoozed one) and send it one message: "News on your PR, not my OK for anything: <the news after the colon>. Handle it as your rules say." A line saying pr-check failed goes in your reply.

## Watching

`watch.json` lists the GitHub sources I want watched: `issues` and `discussions` (GitHub search queries), `projects` (boards as `owner` and `number`), `workflows` (repos whose failed runs count) and `notes` (my free-form sorting notes). Write the query lines yourself from what I ask for, and keep my notes as I wrote them.

Run `bin/watch`. It records news since its last run in `state/incoming.json`, one entry per issue, PR, discussion, board card or run, and prints each as a `watch` line. A new source's first run only records what exists. A `watch-error` line goes in your reply. The board shows entries with status new, needs-you or waiting under Incoming, grouped by effort.

Route each new entry to the effort whose `status.md` Scope line covers it with `bin/incoming set <url> --effort <slug>`, and leave it without an effort otherwise. When several Scope lines cover an entry, route it to the most specific one. A broad scope gets what no narrower scope covers. When that effort has a manager, tell it once per wake-up which entries are new for it, and it sorts them. Sort the rest yourself.

Sorting reads the entry and its news, follows my notes in `watch.json`, and checks the code on the default branch when the entry reports a bug or asks how something works. End it with `bin/incoming set <url>` and one of:
- `--status noise`: nothing for me, like bot updates or news I caused. Later news on it stays noise.
- `--status duplicate --link <url>`: an existing issue, PR or item covers it.
- `--status filed --item <id>`: it's work, filed as a backlog item with `bin/backlog add`.
- `--status waiting`: it waits on someone other than me.
- `--status needs-you --action "<what I have to do, one or two sentences>"`, with `--draft -` and the reply on stdin when an answer from me would help. Write drafts in my voice as `~/.claude/writing-examples.md` shows.

An entry comes back as new when it gets more news. Read only what's new then.

Never post, comment, label, close, assign or move anything on GitHub, and never change a project board or an issue outside `bin/project-sync apply`. Drafts only go on the board, where I copy them.

## Project boards

The boards in `watch.json` track issues, never PRs. Each board's `backlog` names the repo its issues live in. A large effort or topic is a parent issue there that gives the bigger picture: the goal, what's in and out, and the steps as its sub-issues. A backlog item is one of those sub-issues, or a standalone issue for small work, and its `issue` holds that URL (`bin/backlog issue <id> <url>`). Only parent and standalone issues go on a board.

Run `bin/project-sync propose`. It refreshes the proposed card moves (closed issues to Done, cards of started work to In progress, my In progress cards with no activity for two weeks to Later) and prints:
- `candidate <board> <url>`: a started item's issue, or its parent, isn't on the board. Propose it with `bin/project-sync suggest --board <owner/number> --url <url> --status <status> [--field <Name>=<Value>] --why "<one line>"`, following the board's notes in `watch.json`.
- `error <board or id>: ...`: a board or an item's issue couldn't be read. List it in your reply.
- `noissue <id> <title>`: a started item has no issue. When its work belongs on a board, link an issue that already covers it, or draft one with `bin/project-sync draft --repo <backlog repo> --title "<title>" [--parent <url>] --item <id> [--board <owner/number> --status <status>] --why "<one line>"` and the body on stdin. Draft it as a sub-issue under the effort's parent issue when there is one, without a board, and as a standalone issue on the board otherwise. Write titles and bodies in my voice as `~/.claude/writing-examples.md` shows, following the parent's structure.

When a parent issue's picture changed (a step finished, the plan changed, a step was added), propose its new body with `bin/project-sync edit --url <url> --why "<one line>"` and the body on stdin, changing only what changed. Drop open proposals my notes rule out, and any that add a PR, with `bin/project-sync dismiss <id> ...`. Nothing reaches GitHub until I approve it on the board, which sends `apply`.

## Blockers

A blocker is an item id or a note on what an item waits for. `bin/watch` also watches the GitHub issues and PRs that blocker notes link to, and adds `blocks` with the waiting item ids to their `watch` lines. Read the news on such a line, and check each new Incoming entry against the open blockers too: a reply on the issue a blocker names, or a new issue on what it waits for, counts the same way. When news clears a blocker, remove it with `bin/backlog unblock <id> "<blocker>"` and add a desk comment saying what cleared it.

When the last blocker of a paused item with a thread clears, whether GitHub news, a date or the blocking item finishing cleared it, resume that thread as "Starting threads" says, without waiting for Start, since blocking it was my Start for that moment, and list it in your reply. A blocker I remove on the board waits for Start, and an item without a thread stays open for me to start.

## Stale check

On Thursdays, list in the sweep's reply, one line each, what has waited too long:
- questions (`asks`) open for more than two days;
- started items whose open PR has no reviewer requested and no review after three days;
- blockers older than a week, by the comment that added them or the item's date;
- project board proposals open for more than two days.

The board shows old questions under "Getting old" and marks old proposals with their age itself.

## Moving desktop sessions

`/desk move` in the Claude Code desktop app adds an item with `move` (`session`, `checkout`, `branch`, `manager`) for each task it moves, and presses Start for it. A session becomes one item per branch. The session has committed its work, written the brief and freed its branches. `prs` lists every PR, the main one first. For each such `requested` item:
1. Without `manager`: find the T3 project whose folder is `move.checkout`. When there is none, try `t3_project_create`. It needs full access, which you don't have, so when it fails, set `needs` ("Add <folder> as a T3 project, then press Start.") as in "Starting threads".
2. With a `branch`: check that `git -C <checkout> worktree list` shows the branch nowhere, or only at `~/.t3/worktrees/<checkout folder name>/<branch with / as ->` from an earlier try. If one shows it elsewhere, set `needs` and add a desk comment as in "Starting threads", and leave the item `requested`. Otherwise run `git -C <checkout> worktree add <that path> <branch>` when it isn't there yet, and launch with `existing_worktree` on that path. Without a branch, launch as in "Starting threads".
3. With `manager`: launch `manager - <effort>` in this project with `workspaceStrategy` `root` instead, since it becomes the effort's manager.
4. Launch with the title format above and the model from "Starting threads". The message: "You continue Claude desktop session <session>. Read ~/desk/TASK.md, then the `brief` field of ~/desk/backlog/<id>.json in full. Link every PR it names with `link_pull_request` and watch each as ~/.claude/pr-followup.md says. Reply with your branch and last commit, then a short recap (goal, done, left) and the next step. Only take that step when the brief says it needs nothing from me."
5. Wait for its first reply with `t3_thread_wait`. When it confirms its branch, set the item `started` with the thread id and add a desk comment "Moved from desktop session <session> to <thread>". `bin/backlog wait-moved` in the desktop session sees that and archives the session. Then park it, unless it's a manager (step 3), which stays active and pins itself when it asks me something. Parking keeps moved work on the board instead of my sidebar: once the thread's turn has ended, save the question it asks me, if any, in a desk comment, set the item `open` (which clears `asks`) and settle the thread. Pressing Start resumes it. When the reply shows a problem, record the thread id on the item, set `needs` and add a desk comment as in "Starting threads", and leave the item `requested`, so the next Start resumes that thread.

A moved manager rewrites its effort's `status.md` in the format below on its first turn, with the new thread ids in the task table.

## Messages

Send a message only to pass on my decision, to start or resume a thread as "Starting threads" and "Blockers" say, to send a companion its partner's thread id, to tell a settled thread what changed (sweep step 4), to give a service thread work (like a thread that runs device tests), to send `/compact`, to tell a manager about my actions on its effort's items (see "Listening") or its new Incoming entries (see "Watching"), or for one manager to send another work or a finding for its effort. Never send acks, status requests or broadcasts. Messages from a manager never count as my OK to push, post or open a PR, except my own approval passed on unchanged: when I approve actions for several threads at once ("push 3, 5, 7"), send each named thread my exact words.

Notes for another effort go to that effort's manager as one message with a brief, or into a backlog item with that effort when it has no manager. A task files them as backlog items with that effort, and its manager passes on, from the task's final report, the ones that change that effort's current work. For example, a library task that finds a spec ambiguity adds a spec item, and its manager tells the spec effort's manager.

In replies to me, the desk and managers use two verbs for a thread: Start (launch it, or resume it after a pause) and Pause (park and settle it). Don't say settle, unsettle, park or resume to me.

## Compacting

Settle a compacted thread only when sweep step 5 allows it, also when T3 had settled it on its own before. Before settling a thread, make sure what it needs later is in files or commits, then send `/compact`, wait for it with `t3_thread_wait`, and only then settle it. A queued message cancels a pending settle, so the order matters. Skip compacting threads with fewer than about 40 turn items, and threads whose latest run ended over 60 minutes ago, but still settle them when sweep step 5 allows it. `/compact` works on Claude and Codex threads. OpenCode threads show no result for it, so don't compact them.

A thread's prompt cache expires about an hour after its last turn. Compacting before then is cheap, and a compacted thread is cheap to pick up again later, so the desk compacts idle threads at about 50 minutes, whether or not they wait on me. The listener runs `bin/compact-due` every minute, which prints an `idle` event once per run for each thread with a backlog item that is idle 50 minutes to 3 hours and isn't snoozed, settled or waiting on a request. Under `compact` it lists Claude and Codex threads with 40 or more turn items whose cache is still warm, and under `settle` the rest. Under `archive` it lists, once, each thread without a backlog item that has been settled for 7 days, other than the desk, managers, subagents and snoozed threads. It records each run it reported in `state/compacted.json`. For each thread under `compact`, send `/compact`, wait for it, and record the compaction's run id in `compacted.json`. Then settle each listed thread that sweep step 5 allows, after compacting when that step asks for it. Also record the run id of every compaction you send before settling or pausing a thread, so it isn't compacted again. When settling a thread whose latest run is a recorded compaction, don't compact it again. Wherever a rule looks at a thread's last reply, it means the last reply before any compaction.

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
  "created": "2026-10-21",
  "status": "open",
  "thread": null,
  "pr": null,
  "prs": [],
  "issue": null,
  "done": null,
  "comments": [],
  "rank": 3,
  "blockedBy": ["20261020-other-item", "library 4.2 released"],
  "suggested": "One line on why I should do this soon."
}
```

`kind` is bugfix, feature, review, design, test or docs. `label` is user-visible bug, reachable but rare or theoretical. `status` is new (my unsorted capture from the board), open, next (my priority list, ordered by `rank`), requested (I pressed Start on the board), started, done (its PR merged, or I marked it done) or dropped. `blockedBy` lists item ids or notes on what it waits for, and `suggested` marks a desk pick. The last three are optional. Set `blockedBy` only when none of the item can move. Note a part that waits in a comment, and don't block a started item that waits on reviewers, since its settled thread shows that. `issue` is its GitHub issue (see "Project boards"). `pr` is the PR URL and `prs` lists all of them, the main one first, which `bin/board-threads` fills in from the thread's linked PRs, `done` the date it finished or was dropped, and `archived` the date I cleared it from the board's Done column. `asks` holds the question its thread waits on me for (`text` and `at`), which the thread sets and clears with `bin/backlog ask`, and the desk sets or clears when the thread didn't. Task threads create items with status open, except that `/desk` adopts the thread's own item and may pause, finish or drop it. Managers change the rest. Set `needs`, and the `thread` of an item left `requested`, by editing its JSON, since no command sets them. The desk and managers change an item's status only with `bin/backlog status <id> <open|next|started|done|dropped> [--thread <id>] [--pr <url>] --by <desk|manager>`, never by editing the JSON, so the change reaches `state/events.jsonl`. `next` puts it last in Next. The listener ignores the desk's own changes. Add comments with `bin/backlog comment <id> "<text>" --by <desk|manager>`, never by editing the JSON.

A brief uses these `##` sections, in this order, and leaves out the ones that don't apply: Goal, Done when, Plan, Open questions, Evidence (each point labeled verified or inferred), Context (repo, branch, rules, related items, git-ignored files). The board shows Goal and Done when at the top, Open questions in a box, and folds Evidence and Context away. `bin/backlog add` warns when a brief lacks Goal, Done when or Plan.

## Effort status files

`efforts/<effort>/status.md` starts with a `Scope:` line naming the repos, labels or topics the effort covers, which "Watching" routes by, and an `Issue:` line with its parent issue when it has one (see "Project boards"). Its sections, in this order: Resume here, Tasks (table: thread, repo, branch, PR, state, blocked by), Defaults (model and repos), Open decisions, Log (dated, newest last).

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

On the board I can capture notes (status `new`), comment on items, order my Next column, start, pause, finish (Done), drop or reopen items, archive a lane's Done cards, set blockers, change their effort or repo, hide Incoming entries (status dismissed), and apply or dismiss proposed project board changes. The server logs each action to `state/events.jsonl` for `bin/desk-wait`. It never launches anything itself.
