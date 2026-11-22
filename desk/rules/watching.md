## Watching

`watch.json` lists the GitHub sources I want watched: `issues` and `discussions` (GitHub search queries), `projects` (boards as `owner` and `number`), `workflows` (repos whose failed runs count), `prereads` (GitHub search queries for PRs that wait on my review, see "Pre-reads") and `notes` (my free-form sorting notes). Write the query lines yourself from what I ask for, and keep my notes as I wrote them.

Run `bin/watch`. It records news since its last run in `state/incoming.json`, one entry per issue, PR, discussion, board card or run, and prints each as a `watch` line. A new source's first run only records what exists. A `watch-error` line goes in your reply. The board shows entries with status new, needs-you or waiting under Incoming, grouped by effort, except ones I snoozed until a later day (`snoozed`) that got no news but board moves since. `bin/watch` only adds a board move's line to the news of an entry it already has, and prints no line for it. Other entries, except dismissed ones, stay for a day after the last chat message.

Route each new entry to the effort whose `status.md` Scope line covers it with `bin/incoming set <url> --effort <slug>`, and leave it without an effort otherwise. When several Scope lines cover an entry, route it to the most specific one. A broad scope gets what no narrower scope covers. When that effort has a manager and an entry touches its open work (an item's issue or PR, the effort's parent issue, or a PR in a repo where one of its items is started), tell it once per wake-up which entries are new for it, and it sorts them. Sort the rest yourself.

Sorting reads the entry and its news, follows my notes in `watch.json`, and checks the code on the default branch when the entry reports a bug or asks how something works. End it with `bin/incoming set <url>` and one of:
- `--status noise`: nothing for me, like bot updates or news I caused. Later news on it stays noise.
- `--status duplicate --link <url>`: an existing issue, PR or item covers it.
- `--status filed --item <id>`: it's work, filed as a backlog item with `bin/backlog add`.
- `--status waiting`: it waits on someone other than me.
- `--status needs-you --action "<what I have to do, one or two sentences>"`, with `--draft -` and the reply on stdin when an answer from me would help. Write drafts in my voice as `~/.claude/writing-examples.md` shows.

An entry comes back as new when it gets more news. Read only what's new then. When it has a `preread` (see "Pre-reads"), set it needs-you again with the pre-read's `action` and `draft`, unless the news changes what I have to do.

Never post, comment, label, close, assign or move anything on GitHub, and never change a project board or an issue outside `bin/project-sync apply`. Drafts only go on the board, where I copy them.

## Blockers

A blocker is an item id or a note on what an item waits for. `bin/watch` also watches the GitHub issues and PRs that blocker notes link to, and adds `blocks` with the waiting item ids to their `watch` lines. Read the news on such a line, and check each new Incoming entry against the open blockers too: a reply on the issue a blocker names, or a new issue on what it waits for, counts the same way. When news clears a blocker, remove it with `bin/backlog unblock <id> "<blocker>"` and add a desk comment saying what cleared it.

When the last blocker of a paused item with a thread clears, whether GitHub news, a date or the blocking item finishing cleared it, remove it with `bin/backlog unblock` as above. `bin/autostart` then lists the thread to resume, right away with auto-start off and once a slot is free with it on, since blocking it was my Start for that moment. List it in your reply. A blocker I remove on the board waits for Start, and an item without a thread stays open for me to start.
