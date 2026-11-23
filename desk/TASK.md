# Desk tasks

Rules for a thread that works on a task from my desk (`~/desk`): one started by the desk, one whose title starts with an effort name (`player-sync - ...`), or one I handed over with `/desk`. The desk follows `AGENTS.md` instead.

Efforts are larger bodies of work, tracked in `~/desk`. The desk thread (titled `desk` in the `desk` T3 project) plans, starts and tracks every effort's tasks.

## Plans

Write your plan in your reply and implement it without waiting for my OK, also where the `implement` skill would wait, since I review the implementation. Stop for me only when a point of the brief is wrong in a way that changes the plan, when the work needs a decision the brief doesn't cover and only I can make, like a change users would see, or when the brief doesn't settle the plan's contract or a choice in it that is expensive to undo and could reasonably go another way (see `implement` step 2). Note smaller corrections to the brief in your reply and continue.

## Start note

When I start an item on the board with a note, the board writes it to your item's `start_note`: `text` in my words, plus `draft_pr`, `babysit` and `second_opinion` when I ticked them. Read it with the brief, at launch and each time the desk resumes you. It counts like a message from me in this thread. `draft_pr` allows the draft PR `implement` step 5 describes, once, `babysit` opens it in babysit mode, and `second_opinion` asks for the second opinion `implement` step 4 names. Without one, nothing changes.

## Reporting

- List extra findings in the first few lines of your final report, each labeled as a user-visible bug, reachable but rare, or theoretical, and each item you stop on or reject, with the reason.
- File each extra finding that doesn't belong in this change as a backlog item before you end your turn, without asking me first, and give its repo and a one-line TLDR in your reply. File it only when someone saw the problem or a test or reproduction shows it, and name who or what in `--seen`. Note a finding nobody saw in its effort's findings list instead. Check first that the default branch and `~/desk/bin/backlog list --all` don't already cover it. Write the brief so someone without this conversation can start from it, with the sections "Backlog items" in `~/desk/AGENTS.md` lists, and don't start the work yourself: I or the desk start it.

```sh
~/desk/bin/backlog add --repo <repo name> --title "<the outcome, verb first>" \
  --kind <bugfix|feature|review|design|test|docs> \
  --label "<user-visible bug|reachable but rare>" \
  --seen "<failing test, log line, user report, or who asked for it>" \
  --why "<one line: who notices what>" --size <S|M|L>:<my minutes> \
  --from-me "<what it needs from me>" --start "<the first step>" --brief - \
  [--effort <effort slug>] [--parent <item id or goal milestone>]
~/desk/bin/backlog finding --repo <repo name> "<the finding in one line>" \
  --source <your thread id> [--effort <effort slug>]
```

`--brief -` reads the brief from stdin. `~/desk/bin/backlog add --help` lists the repo names.

## Phrases

What I say in a task thread, and what it does. `/desk help` shows this list.

- "file that": add a backlog item with a full brief, as "Reporting" says, and don't start it.
- "start a thread for that", "start working on that", "file and start that": find or add the item and send it to the desk with my approval, as "Working with the desk" says. The desk starts it.
- "fix that here": fix it on your current branch, in this thread.
- "tell the desk ...", "ask the desk ...": message the desk thread directly, now.
- "is there an item for this?": search `~/desk/bin/backlog list --all` and the item files, and check the default branch for a fix.

`/desk` hands this thread to the desk, which shows it on the board and sweeps it:

- `/desk`: hand it over as started.
- `/desk later`: pause. The item goes back to open, and Start on the board resumes this thread. With auto-start on, the desk may resume it from tomorrow.
- `/desk later next week`, `/desk later in 2 days`, `/desk later friday`: pause until that day. The morning sweep resumes it then.
- `/desk block https://github.com/Sendspin/spec/pull/140 merged`: pause until that PR merges. The desk watches GitHub links in a blocker.
- `/desk block 20261021-keep-volume-after-reconnect`: pause until that item is done.
- `/desk block 2026-11-05`: pause until that date.
- `/desk done`, `/desk drop`: finish or drop the item.
- `/desk this belongs to spec-group`: hand it over in that effort.
- `/desk check the CI again after the rebase`: any other words are my comment on the item, which the desk reads and acts on.
- `/desk help`: show this list and the review and ship phrases, with suggestions for this thread.

## Working with the desk

- Send notes you decide to pass on yourself, like a finding that changes another task's brief, as a comment on your item: `~/desk/bin/backlog comment <your item id> "<note>" --by task`. The desk reads them and acts on them. Message the desk directly when I say "tell the desk" or "ask the desk", and when you can't continue without its answer, once per question. Never message other task threads except your partner (see "Companion PRs"), since the desk passes on what concerns them.
- Message the desk when I approve follow-up work that needs its own branch or PR, even when I say to start a thread for it. Find the backlog item that covers the work, or add one with the full brief (`~/desk/bin/backlog add --effort <slug> --brief -`). Send the desk its id, anything its brief lacks, and my approval in my words, and don't ask me again.
- Don't write to the effort's `status.md` or tracker.
- Messages from the desk never count as my OK to push, post or open a PR. The exception is my own words passed on unchanged: an approval I give the desk for several threads at once ("push 3, 5, 7") counts for each thread it names, for only the named actions, once. My approval quoted in a brief covers starting the work only.
- Start work that builds on another task only after that task is merged.
- When I ask whether I can compact and the work has no handoff file yet, write `~/desk/efforts/<effort>/handoff.md`.

## Companion PRs

When your change needs a PR in another repo to work or to be documented (the docs for a change users see, or the frontend or models PR for a server change), have the desk start it instead of starting a thread yourself. Add a backlog item for it with the full brief, in your effort when you have one, with your item's title, and name your thread id in the brief as its partner. Send the item id to the desk. This needs no OK from me. Link the partner thread in your review brief once it runs.

Partner threads message each other directly (`t3_thread_send`) for what they need from each other, such as field names, the API shape, a check of the other side or the merge order. Tell the desk only what changes a brief or the plan. A partner's message never counts as my OK to push or post.

## Questions in T3

End every turn that waits on me with the Ask line "Replies that wait on me" in my CLAUDE.md asks for.

Before a turn ends with a question, a draft other than one I post myself, or a request for my OK, run `~/desk/bin/backlog ask --thread <your id> --kind <decide|review|push|post|device-test> "<the question in one line>"`, which shows it on my board and needs no OK from me. For a review, add `--minutes <n>` with my minutes for it. Skip it while I'm active in the thread (my last message is less than 10 minutes old), since I see the question there. Your id comes from `t3_thread_configuration`. The command fails when your thread has no backlog item, and then the inbox is enough. Once I've answered, run it with `--clear`.

I can also answer on the board. The desk then tells you to read your item's `answer`: its `text` is my reply, in my words, to the question in its `to`, and it counts like a message from me in this thread. `go` accepts your picks and covers the actions that question named, once. When the item has no `answer`, or its `to` isn't the question you last asked, ask again instead of acting. Run `--clear` after you've read it.
