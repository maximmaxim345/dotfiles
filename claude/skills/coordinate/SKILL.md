---
name: coordinate
description: Run this session as the coordinator of a group of task sessions (names, sidebar group, status file, briefs, relays).
argument-hint: "<effort to start, or the name of one to resume>"
disable-model-invocation: true
---

Effort: $ARGUMENTS

This session coordinates. It plans, starts and tracks task sessions and checks their claims, and does little coding itself. Task sessions follow "Coordinated sessions" in my CLAUDE.md.

## 1. Set up

- If `~/.claude/handoffs/` has a folder for this effort, resume it: read its `status.md`, check it against `list_sessions` (archived ones too), git and gh, and tell me where things stand. Skip the rest of this section.
- Rename this session to `meta - <repos> - <effort>` with `set_session_title`. Use short repo names: aio (aiosendspin), ma (music-assistant server), fe (music-assistant frontend), cpp (sendspin-cpp), cliairplay (airplay-cli), spec (Sendspin spec), js (sendspin-js), cli (sendspin-cli).
- Put this session in one sidebar group for the effort. Offer an existing group that fits or a new one named after the effort, and create or move after my OK.
- Create `~/.claude/handoffs/<effort-slug>/` with `status.md` and a `briefs/` folder, and add a project memory note that points at the folder.

## 2. Plan

Propose the task list before starting anything: number, type, repo, title, what it depends on, and its done criteria. Order it the way I should review it, library fixes before the code that uses them. Wait for my OK.

## 3. Start tasks

- Name task sessions `<n> - <type> - <repo> - <title>`, with a short imperative title, under 60 characters in all. Type is one of bugfix, feature, review, design, test or docs, or a type I name. Work outside the plan gets `side - <repo> - <title>`.
- Start at most four task sessions at a time, and split a bigger batch into parts.
- Write each brief to `briefs/<n>.md`, then start the session with `spawn_task` and the brief as its prompt. Set `cwd` to the main checkout of the task's repo. When there's no local copy, clone it next to my other clones under `~/projects/` first. Once I start the session, check its title and group and fix them.
- Each brief has:
  - `First run: git checkout <branch>` as its first line when it continues existing work.
  - `You are task <n> of a coordinated group. Coordinator: <this session's exact name>. Follow 'Coordinated sessions' in your CLAUDE.md.`
  - The repo's project rules file to read.
  - The evidence (file and line, log paths, spec quotes), each piece labeled verified or inferred.
  - The plan, the done criteria, and "confirm each item before changing code and stop on any that isn't real".
  - Recorded decisions, related sessions, expected conflicts and dependencies.
- Leave out rules every session already loads from my CLAUDE.md, and never tell a session to create a worktree.

## 4. Run the group

- Check what task sessions report in the code, git or gh before relaying it. Answer their questions directly when you can, but never answer a go-ahead to push, post or open a PR.
- Relay to me in one line per status change. Give detail only where I must decide, numbered, with your recommendation.
- Extra findings from task sessions come to you. Drop duplicates of the plan and of open sessions, skip theoretical ones, and propose a new task or a fold into an existing one.
- Keep `status.md` current after every change. It holds one table (n, session, repo, branch, commits, PR, state, blocked by), the open decisions, and a dated list of the decisions made. Only this session writes it.
- When I ask where things stand, rebuild the answer from `list_sessions`, git and gh, never from memory, and correct `status.md` where it differs. For library fixes, track merged, released and pinned separately.
- After a merge, tell the sessions whose branches depend on it to rebase.
- When I test on real devices, a separate test session gets a test plan from you (steps, what to listen for, log patterns per fix), and you turn failures into tasks.
- Show state in session names. When my real-device test passes, put `passed` after the number. A blocked session becomes `parked until <condition in plain words> - <repo> - <title>`. When priorities change, propose the full renamed list and apply it with `set_session_title` after my OK.
- Archive sessions only with my OK. Keep this session unarchived while task sessions use files in its folder.

## 5. Move a session to another repo

When a task session runs in the wrong repo, ask it for a handoff, including the full prompts of any chips it suggested. Have it commit unfinished work as `wip:` and remove its worktree so the branch is free. Then start a new session with the right `cwd` and the handoff as its brief, which says the `wip:` commit is real work to finish, and archive the old one after my OK.

## 6. Before compacting

Update `status.md` and the memory note. Then tell me I can compact, with a `/compact Keep: ...` line and the message to send afterwards (`/coordinate <effort-slug>`).
