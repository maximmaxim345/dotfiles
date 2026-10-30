---
name: ma-dev
description: Start a Music Assistant dev server, and the frontend when needed, on a copy of my configured data folder with working streaming providers and players. Use when a Music Assistant test or reproduction needs real providers, players, or library data.
argument-hint: "[setup|frontend]"
---

Start a Music Assistant server from the current server checkout or worktree, on a copy of `~/.musicassistant`. That folder is logged in to my streaming providers, so the copy works without setup. Never point a server at `~/.musicassistant` itself.

## Backend

Run these from the server checkout or worktree for this task (default `~/projects/music-assistant/server`):

1. If `.venv` is missing, run `scripts/setup.sh`.
2. If `.claude/ma-data` is missing, copy the data folder without its cache, logs, and backups. The repo's `.gitignore` covers `.claude/`, so the copy and its tokens stay out of git.
   ```bash
   rsync -a --exclude .cache --exclude 'musicassistant.log*' --exclude '*.backup' ~/.musicassistant/ .claude/ma-data/
   ```
   Reuse an existing copy so its state survives restarts. Delete it to start fresh.
3. Pick the ports. The web port (default 8095) and the stream port (default 8097) are settings in the copy's `settings.json`, with no flag or environment variable for them. The Sendspin port (default 8927) is a server constant, which the start command below overrides. The main checkout uses 8095, 8097 and 8927. A worktree uses the first set of 8195, 8197 and 9027, then 8295, 8297 and 9127, and so on where all three are free. Keep the web and stream ports the copy already has (`jq '.core.webserver.values.bind_port, .core.streams.values.bind_port' .claude/ma-data/settings.json`) while they're free. Check a port with `lsof -nP -iTCP:<port> -sTCP:LISTEN`, and if another server holds it, see "Other servers" below. Write the web and stream ports while the server is stopped:
   ```bash
   jq --argjson web <web port> --argjson stream <stream port> '.core.webserver.values.bind_port = $web | .core.streams.values.bind_port = $stream' .claude/ma-data/settings.json > .claude/settings.tmp && mv .claude/settings.tmp .claude/ma-data/settings.json
   ```
4. Start the server in the background. `MASS_APP_VARS_FILE` provides the bundled provider credentials. The `-c` wrapper sets the Sendspin port before the server imports it, so the checkout stays unchanged.
   ```bash
   PYTHONDEVMODE=1 MASS_APP_VARS_FILE="$HOME/projects/music-assistant/appvars/app_vars.json" .venv/bin/python -c 'import sys, runpy, music_assistant.constants as c; c.SENDSPIN_SERVER_PORT = int(sys.argv.pop(1)); runpy.run_module("music_assistant", run_name="__main__", alter_sys=True)' <sendspin port> --log-level debug --data-dir .claude/ma-data --cache-dir .claude/ma-data/.cache
   ```
5. Once the web port listens, write `.claude/ma-dev.json` with this thread's id from `t3_thread_configuration` (the session title outside T3 Code), the server's pid from `lsof -t -nP -iTCP:<web port> -sTCP:LISTEN`, and the ports, like `{"thread": "<id>", "pid": 12345, "web_port": 8195, "stream_port": 8197, "sendspin_port": 9027}`. Delete it when you stop the server.

The server's built-in UI is at `http://localhost:<web port>`. Speakers get their stream URLs from the server, so they follow the stream port without changes. Two servers on copies of the same data see and control the same speakers, so don't test on a speaker another server is playing to.

With `setup`, do steps 1 to 3 and start nothing, not even the frontend, then give me the VS Code line below so I can start it with F5. An F5 run uses Sendspin port 8927, so when another server holds 8927, tell me that this server's Sendspin provider and browser player won't work.

## Players

Test with the "Demo Sendspin Clients" provider (`_demo_sendspin_clients`), which runs in dev mode only. Its fake Sendspin speakers connect to this server, show up as normal Sendspin players, and decode and drop the audio, so nothing plays out loud. Enable it in the copy, in the built-in UI or through the API with the administrator login, and pick the scenarios the test needs. Watch them through the server log and the provider's settings page.

Ask me before playing to, grouping, or changing a real speaker, every time.

## Other servers

A server that holds a port you need belongs to its owner. Find the owner: take the pid from `lsof`, its folder from `lsof -a -p <pid> -d cwd -Fn`, and read `.claude/ma-dev.json` there. Stop it only when that file names this thread and the same pid. When it names another thread, or there is no file or another pid (often my own F5 run), tell me whose server it is and ask instead of stopping it. Never copy another server's data.

## Logging in

The data folder has three test logins, only for local test servers, so put them in scripts and commands as is:

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `dev-test-admin` | `dev-test-admin` |
| User | `dev-test-user` | `dev-test-user` |
| Guest | `dev-test-guest` | `dev-test-guest` |

Use the administrator unless the test is about what a user or guest may do. Log in and keep the token in `.claude/ma-token`:
```bash
curl -sf -H 'Content-Type: application/json' -d '{"provider_id": "builtin", "credentials": {"username": "dev-test-admin", "password": "dev-test-admin"}}' http://localhost:<web port>/auth/login | jq -r .token > .claude/ma-token
```
Log in again after a fresh copy or when the token stops working. If `.claude/ma-token` comes out empty, tell me the login failed.

## Frontend

Start it only when the task touches the frontend or I pass `frontend`. The built-in UI covers everything else.

1. In the frontend checkout or worktree for this task (default `~/projects/music-assistant/frontend`), run `pnpm install`, then start `pnpm dev` in the background.
2. Open the URL Vite prints, usually http://localhost:3000. When it asks for the server address, give `http://localhost:<web port>`.
3. Go through the changed screens with a headless Playwright script (the browsers are in `~/Library/Caches/ms-playwright`), in light and dark mode, and save screenshots to `.claude/screenshots/` in the frontend worktree. Name each file after the screen and state it shows, and list the paths in the brief.

## Debugging in VS Code

The server's `.vscode/launch.json` is tracked and runs on `~/.musicassistant`, so don't edit it. When I want to debug on the copy, or after `setup`, tell me to add `"--data-dir", "${workspaceFolder}/.claude/ma-data", "--cache-dir", "${workspaceFolder}/.claude/ma-data/.cache"` to the "Music Assistant: Server" arguments myself.

## Hand back

Say what's running, on which web, stream and Sendspin ports and data folder, and how to stop it. After `setup`, say what was prepared instead.

Stop the servers and clients you started once I report the test result or approve the push, and say so in one line.
