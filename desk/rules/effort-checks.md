## Effort checks

An effort check lets the desk cover an effort without a manager thread. A subagent reads the effort's `status.md` and as much code as the question needs, brings the file up to date and ends. The file is the effort's memory, so nothing the next check needs may stay only in a reply.

Run one for an effort without a manager when a wake-up, a sweep or a message of mine brings one of these:
- a task's note for it (a comment with `"by": "task"`), or follow-up work a task sent (run the check first, then start the work as "Starting threads" says);
- one of its items became done or dropped while the effort has other open or started items;
- you removed the last blocker of one of its items;
- I ask about its plan, its state or what to do next.

Handle everything else yourself without one: a start, a pause, PR news, a task row. Run at most one check per effort in a turn, with all its events together.

Start one subagent on your own model and effort, wait for it, and give it this prompt: "Effort check for <effort>: read ~/desk/rules/effort-checks.md and do "In the check". Events: <one line each, with the item ids, and the path of the repo's main checkout or the task's worktree>." Then do what its reply asks of the desk, as these rules say for the desk, and pass on to me only what needs me.

### In the check

You are the subagent. Read anything you need. Write only the files in `efforts/<effort>/`, and the backlog through `bin/backlog`. Never start, message, settle or archive a thread, never change an item's status, and never push, post or comment on GitHub.
1. Read the effort's `status.md` in full, the open and started items among the files in `backlog/` whose `effort` is this one, and the comments the events name.
2. Check what the events claim in the code, git and `gh`, in the checkouts the events name, without changing them. Read as far as the plan depends on it and no further.
3. Update `status.md` in the sections "Effort status files" in `AGENTS.md` lists, with one dated Log line per event that says what the task found or what changed. Keep what a later check can't get back from the code or the items, and nothing else.
4. Turn follow-ups into backlog items (see "Backlog items" in `AGENTS.md`), and add a comment with `--by desk` on each item you would block or drop, with the reason in one line.
5. Reply in at most five lines: what changed in the plan, the items you filed, what the desk must do (a thread to start or resume that I already approved, a message to pass on, a desk pick to set or remove, a blocker to set, an item to drop), and what needs me, with your pick.

### Retiring a manager

When I say an effort no longer needs its manager:
1. Send the manager one message: "Maxim retires this manager thread, and the desk covers the effort from its status file from now on. Write everything a reader of only `status.md` needs into it, in the sections "Effort status files" in ~/desk/AGENTS.md lists: the plan and its order, each decision with its reason and the option that lost, what each task found, and the open questions. Link the other files of the effort folder that still matter. Reply "written" when it's done, and start nothing." Wait for its turn with `t3_thread_wait` and read the reply.
2. Start a subagent with: "Read only ~/desk/efforts/<effort>/status.md, the files it links and the effort's backlog items. Say in ten lines what the effort's next three steps are and why, and what you couldn't tell from the file." Send its answer to the manager unchanged, and ask what is wrong or missing and to fix the file, and wait for its turn the same way. Repeat this step once when the manager changed the plan.
3. Archive the manager thread, mark its own item done when it has one, run `bin/board-threads`, and add a Log line to `status.md`.
