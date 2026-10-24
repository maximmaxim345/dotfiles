---
name: ma-device-test
description: Test Music Assistant changes on my real speakers, on a local dev server or a remote instance, by working through a checklist with me. Use when I ask to test branches, PRs or a stable backport on real hardware, or to check playback, sync, grouping or pairing by ear.
argument-hint: "[what to test]"
---

Test: $ARGUMENTS

I listen and handle the hardware. You build the test setup, run everything that can run without me, read the logs after every step, and keep track of the results.

## 1. Plan the round

1. List what's under test: each branch or PR, and any change in another repo the round includes. When I name the sessions that own the changes, ask each one where its branch or commit is, what to test, and which log lines show it working or failing. Don't message any other session.
2. Write the checklist: one line per item with what I do, what I should hear, and what you check in the log. Mark each item as automated (WS API, test clients, log checks) or as mine (listening, unplugging, flashing firmware, steps in the web UI).
3. Show me the checklist and the order, and wait for my OK. Each item ends as passed, failed or skipped with a reason.

## 2. Build the test setup

Locally, in the session's server worktree:

- Make a local branch `wip/test-<slug>` from a freshly fetched `origin/dev` and merge each branch under test. Never push it. Keep a second branch on plain `origin/dev` when the round needs A/B runs.
- When the round includes a change to a library or a bundled binary, ask the session that owns it, or me, how to install that build. Back up whatever you replace.
- Start the server with the `ma-dev` skill.

To test on a Home Assistant instance or another remote server, ask me for access and for how its build is switched.

## 3. Run it

- Set the providers under test to debug with `config/providers/save`, passing `provider_domain`, `instance_id` and `values: {"log_level": "DEBUG"}`, and note each one so you can reset it.
- One item at a time: say what I should do and what to listen for, run the automated part, wait for what I heard, then check the log for that time window before the next item. Note the log line count or timestamp at each step.
- Write the helper scripts the round needs in the scratchpad, fitted to the checklist and the current APIs. Run them with `uv run` and PEP 723 headers, so each one brings its own dependencies.
  - WS API: connect to `ws://<host>:<web port>/ws` (8095 unless `ma-dev` gave the server other ports), read the server info message, send `auth` with a token, then send commands with a `message_id` each. Locally, log in as the `ma-dev` skill's "Logging in" part says, which reads my login from `~/.config/ma-dev/login.env` and keeps the token in `.claude/ma-token`. Never print the token, and never ask me to paste a login or token in chat.
  - Logs: `logging/get` returns the whole `musicassistant.log` when you can't tail it.
  - Headless Sendspin client: build it on `aiosendspin.client.SendspinClient` with a persistent identity key and pairing store, connecting to `ws://<host>:8927/sendspin`. Write every event to a JSON lines file, then check it for position jumps, positions past the track end, and audio gaps. Use an aiosendspin version that can handshake with the server's.
- Before a server restart or a rollback, save `players/all` and the provider list, so you can compare afterwards.
- Before saying a bug reproduced, compare against plain dev or stable. Before blaming the change, check whether the same thing happens without it.

## 4. Report

Write the report in the chat:

- The verdict in one sentence.
- Each checklist item with its result.
- Each finding, labeled as a regression from the change under test or as already on dev or stable, and as a user-visible bug, reachable but rare, or theoretical. For the ones that need a fix, give a proposed task title starting with a shared prefix, such as `found in backport test - `.
- What wasn't covered, and why.

Then ask whether to send the report to the session that owns the merged branch. In a desk task, also ask whether that session should add the follow-up tasks as backlog items. Send nothing until I say yes.

## 5. Clean up

Ask before each step that touches something I set up:

- Remove the test groups and test players you created.
- Reset every log level you changed to `GLOBAL`.
- Put back every library and binary you replaced, and run `scripts/setup.sh` when the venv still has a test build.

## Known traps

- MA runs a pause on a Sendspin player as a STOP. The UI keeps the paused position, so 0:00 while paused is a regression.
- A dynamic leader switch only happens through a sync group player.
- A script that does its work at import time runs again when another script imports it. Keep reusable code in modules with a `__main__` guard.
- Bridged speakers can register late or under a temporary id while the Cast and AirPlay bridges settle. Wait for the player before calling `play_media`, since a call to a missing player fails with "There is nothing to play here".
