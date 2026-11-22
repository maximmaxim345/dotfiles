## Sweep

1. List threads in all projects, settled and snoozed ones included, with their linked PRs.
2. Leave threads without a backlog item alone (see "Thread lifecycle"). The board lists them, as unassigned when their title names no effort.
3. Read every linked PR of a thread with a backlog item with `gh`: state, checks, mergeable, and reviews or comments by people other than me and bots.
4. Do "PR check".
5. Compact, then settle, each thread with a backlog item that isn't snoozed, has been idle for 50 minutes or more, and waits only on others: it has an open PR or its last reply says what it waits on, no reply since my last message asks me something or says the work is finished (step 7 handles those), its item has no `asks`, and no review round is running (see "Compacting"). The 50 minutes keep a thread I'm working with between messages. Settling ends a thread's T3 PR watch, so later news reaches it through step 4. A thread that watches with `bin/pr-check --wait` may hear the same news twice, which it handles once. When a thread with a backlog item that isn't running, snoozed or settled has linked PRs and a reply since my last message asks me something or its item has `asks`, however long it has been idle, call `unwatch_pull_request` with its thread id for each of them, since a watched thread stays in my Working list instead of my inbox. Settle a thread with a PR it doesn't watch only in a full sweep (not a refresh or `idle`), after reading the PR with `gh`. Managers settle themselves (see "Managers"). A manager whose item has no `asks` and that asked me nothing since my last message that only its thread can answer (see "Managers") counts as waiting on others: unpin it and settle it without compacting it, since pinning unsettles a thread.
6. Archive settled and snoozed threads with a backlog item whose PR closed, or merged without step 8 marking the item done, more than a day ago. Mark their task row and backlog item done with the date, the PR and the thread id.
7. Read the thread of every `started` item (`t3_thread_read`). When the thread is archived or gone, mark the item done with today's date and add a desk comment that it was closed outside the desk. When the thread isn't snoozed, is idle and has no PR, and its last reply says the work is finished, list it in `needsYou` with the why "finished? mark it done on the board". When the thread isn't snoozed, a reply since my last message asks me something (for a manager, something only its thread can answer, see "Managers"), and the item has no `asks`, set it with `bin/backlog ask --thread <id> "<the question in one line>"`. When the item has `asks` and I answered in the thread after `asks.at`, with no later reply asking me something, clear it with `bin/backlog ask --thread <id> --clear`. Unsettle a settled thread whose item has `asks`, since a settled thread leaves my inbox. When the thread isn't a manager, is settled, isn't in `state/parked.json`, has no open PR, its item has no blocker, and its last reply neither says it waits on someone else nor that the work is finished, I settled it by hand to put it aside: pause the item with `bin/backlog status <id> open --by desk`, which keeps its thread.
8. Run `bin/board-threads`, which rebuilds `state/threads.json` from T3's database and the backlog and prints the entries that changed, then fix any new `needsYou` why that is wrong (see "Board"). It also copies the PRs a thread linked into its item (`+pr` lines), and marks a started item done once all its PRs merged (`done` lines), and adds items for threads of mine that started work outside the desk (`adopt` lines, see "Thread lifecycle"). For each `adopt` line, fill in the item's effort, kind and why from the thread, without messaging it. For each `done` line, archive the item's thread without compacting, after waiting for a running turn as for my `done` events, mark its task row done unless the effort has a manager, and tell that manager as for my own changes (see "Listening"). Read `threads.json` only when you need more than that. When it fails because T3's database changed, call `t3_thread_list` for every project, settled and snoozed included, and pipe the results into `bin/board-threads --stdin`. Then reply with what needs me, in priority order, one line each.
9. Sort my captures (status `new`, my raw notes in `brief`): turn each into one or more proper items, one per idea, with title, kind, label, repo, effort, why, seen, size, minutes, fromMe, start and brief, status `open`, and the original note quoted in a desk comment. When a capture becomes one item, run `bin/backlog reslug <id>` after giving it its title, fix the effort files it lists, and tell a started thread its brief's new path. Keep a repo or effort I picked, unless my note says I'm unsure of it: then check where the code lives and pick that repo, saying why in the comment. When a note is too unclear to sort, leave it `new` and ask in a comment.
10. Triage open backlog items: set the repo name and the effort, drop duplicates and items whose fix is already on the default branch (with a comment saying why), and fill in missing briefs. Set `blockedBy` when none of an item can move before another item or an outside event, and remove blockers that no longer hold, also on started items, as "Blockers" says. A blocker that names a date holds until that date: on it, remove the blocker, add a desk comment and list the item in your reply, and resume its thread as "Blockers" says when it was the last one. Mark up to five open items I should do soon with `suggested` (a one-line reason) and remove it from items that no longer fit. In efforts with a manager, leave `suggested` to the manager. Move items into Next only when my note or message asks for it, and put them last, since that column is my order.
11. Answer new comments on backlog items (`"by": "me"`) with a comment of your own (`"by": "desk"`), and apply what they ask that needs no launch.
12. Do "Watching", then "Project boards".
13. In the first sweep of a month, summarize last month's lines from `findings.md` and every effort's `findings.md` for me in a few lines. File an item only for the ones I pick.

At the end of a sweep, do "Spaces", then run `bin/desk-wait --refreshed`, since the sweep covers a refresh.

Base every state on threads, git and `gh`, never on memory, and fix `status.md` where it differs. Take dates and times from `date`, never from memory.

## Refresh

On weekdays from 8:00 to 20:00, the listener queues `refresh` when the last refresh was 45 minutes ago or more. A refresh is a short sweep that keeps the board's thread lists and Incoming current: do sweep steps 1, 2, 4, 5, 7 and 8, read PRs only through `bin/pr-check`, and do "Watching" and "Spaces". Reply once, when it's done: one line for the threads, plus one line per entry you set to needs-you, and stay silent when nothing changed. Leave out questions other threads asked me, since their threads and the board show them.

## PR check

Settled threads don't watch their PRs, so the desk passes on their PR news.
1. List all projects, and in each the settled threads with linked PRs and a backlog item.
2. Run `bin/pr-check <thread id>=<PR url> ...` once with all of them. It prints news since its last run, and a merge or close on every run: reviews and comments by people other than me and bots, conflicts, failed checks, merges and closes.
3. For each line it prints: a PR merged or closed more than a day ago gets sweep step 6. On any other news, except a merge or close from the last day, unsettle the thread (never a snoozed one) and send it one message: "News on your PR, not my OK for anything: <the news after the colon>. Handle it as your rules say." When the item's space is off, add the news as a desk comment on the item and run `bin/space-sync --hold <thread> "<the news>"` instead, which passes it on once the space is on again. A line saying pr-check failed goes in your reply.

## Stale check

In each morning sweep, list in the reply, one line each with its age, what has waited on me for more than three days:
- questions (`asks`), by `asks.at`;
- Incoming entries with status needs-you, by `updated`;
- open project board proposals, by `at`.

On Thursdays, also list:
- started items whose open PR has no reviewer requested and no review after three days;
- blockers older than a week, by the comment that added them or the item's date.

On Thursdays, also run `bin/worktree-due`, which takes a few minutes. It prints archived threads with a backlog item that were archived 14 days ago or more: `due` when their worktree has no uncommitted changes and every commit is on a remote branch, `held` with the reason otherwise. List the `due` threads in one block for me to delete in T3, then each `held` one with its reason.

The board shows old questions under "Getting old" and marks old proposals with their age itself.
