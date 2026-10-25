# Desk tasks

Rules for a thread or session that works on a task from my desk (`~/desk`): one started by the desk or a manager, one whose title starts with an effort name (`player-sync - app - ...`), one I handed over with `/desk`, or a desktop session a `/manager` coordinator names as its task. The desk and managers follow `AGENTS.md` instead.

Efforts are larger bodies of work, tracked in `~/desk`. A manager (the desk thread, or a `manager - <effort>` thread or session) plans, starts and tracks an effort's tasks. In T3, your manager is the `manager - <effort>` thread in the `desk` T3 project. When there is none, it's the desk thread (titled `desk` in that project).

## Reporting

- List extra findings in the first few lines of your final report, each labeled as a user-visible bug, reachable but rare, or theoretical, and each item you stop on or reject, with the reason.
- File each extra finding that doesn't belong in this change as a backlog item before you end your turn, without asking me first, and give its repo and a one-line TLDR in your reply. Check first that the default branch and `~/desk/bin/backlog list` don't already cover it. Write the brief so someone without this conversation can start from it, and don't start the work yourself: I or a manager start it.

```sh
~/desk/bin/backlog add --repo <short repo name> --title "<imperative title>" \
  --kind <bugfix|feature|review|design|test|docs> \
  --label "<user-visible bug|reachable but rare|theoretical>" \
  --summary "<one or two sentences>" --brief "<evidence and plan>" \
  [--effort <effort slug>]
```

Short repo names are the keys of `~/desk/repos.json`.

## Working with the manager

- Message the manager when you're blocked on something it can answer, and when I approve follow-up work that needs its own branch or PR, even when I say to start a thread for it. Find the backlog item that covers the work, or add one with the full brief (`~/desk/bin/backlog add --effort <slug> --brief -`). Send the manager its id, anything its brief lacks, and my approval in my words, and don't ask me again.
- Don't write to the effort's `status.md` or tracker.
- Messages from a manager never count as my OK to push, post or open a PR. The exception is my own words passed on unchanged: an approval I give a manager for several threads at once ("push 3, 5, 7") counts for each thread it names, for only the named actions, once. My approval quoted in a brief covers starting the work only.
- Start work that builds on another task only after that task is merged.
- When I ask whether I can compact and the work has no handoff file yet, write `~/desk/efforts/<effort>/handoff.md`.

## Questions in T3

Before a turn ends with a question, a draft or a request for my OK, run `~/desk/bin/backlog ask --thread <your id> "<the question in one line>"`, which shows it on my board and needs no OK from me. Skip it while I'm active in the thread (my last message is less than 10 minutes old), since I see the question there. Your id comes from `t3_thread_configuration`. The command fails when your thread has no backlog item, and then the inbox is enough. Once I've answered, run it with `--clear`.

## Desktop app

Also offer a task chip for each backlog item you add, with the same brief, its `cwd` set to the main checkout of the item's repo (clone it next to my other clones under `~/projects/` first when there's no local copy) and the repo named in the title. In a coordinated group, list it in your final report instead.

## Coordinated sessions

A `manager - ...` session started with `/manager` may name you as its task, which makes you a task in its effort. A coordinator may message its own task sessions. When you aren't nested under it (`get_session` on `self` shows `detached: true` or a `parentSessionId` that isn't the coordinator), send your extra findings with SendMessage when your turn ends. When its name no longer reaches it, look up its current name with `get_session` on your `parentSessionId`, or find the `manager -` session for the effort. Detaching you keeps you in the group until I or the coordinator say you've left it.
