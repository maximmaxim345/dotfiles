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
3. Pick the ports. The web port (default 8095) and the stream port (default 8097) are settings in the copy's `settings.json`, with no flag or environment variable for them. The main checkout uses 8095 and 8097. A worktree uses the first pair of 8195 and 8197, 8295 and 8297, and so on where both ports are free. Keep the ports the copy already has (`jq '.core.webserver.values.bind_port, .core.streams.values.bind_port' .claude/ma-data/settings.json`) while they're free. Check a port with `lsof -nP -iTCP:<port> -sTCP:LISTEN`, and if another server holds it, see "Other servers" below. Write the ports while the server is stopped:
   ```bash
   jq --argjson web <web port> --argjson stream <stream port> '.core.webserver.values.bind_port = $web | .core.streams.values.bind_port = $stream' .claude/ma-data/settings.json > .claude/settings.tmp && mv .claude/settings.tmp .claude/ma-data/settings.json
   ```
4. Check the Sendspin port 8927. It's fixed in the server, so only one server on this machine can run Sendspin players and the browser player. If another server holds it, tell me before starting, since this server's Sendspin provider would fail to load and its browser player would land on the other server.
5. Start the server in the background. `MASS_APP_VARS_FILE` provides the bundled provider credentials.
   ```bash
   PYTHONDEVMODE=1 MASS_APP_VARS_FILE="$HOME/projects/music-assistant/appvars/app_vars.json" .venv/bin/python -m music_assistant --log-level debug --data-dir .claude/ma-data
   ```
6. Once the web port listens, write `.claude/ma-dev.json` with this thread's id from `t3_thread_configuration` (the session title outside T3 Code), the server's pid from `lsof -t -nP -iTCP:<web port> -sTCP:LISTEN`, and the ports, like `{"thread": "<id>", "pid": 12345, "web_port": 8195, "stream_port": 8197}`. Delete it when you stop the server.

The server's built-in UI is at `http://localhost:<web port>`. Speakers get their stream URLs from the server, so they follow the stream port without changes. Two servers on copies of the same data see and control the same speakers, so don't test on a speaker another server is playing to.

With `setup`, do steps 1 to 4 and start nothing, not even the frontend, then give me the VS Code line below so I can start it with F5.

## Other servers

A server that holds a port you need belongs to its owner. Find the owner: take the pid from `lsof`, its folder from `lsof -a -p <pid> -d cwd -Fn`, and read `.claude/ma-dev.json` there. Stop it only when that file names this thread. When it names another thread, or there is no file (often my own F5 run), tell me whose server it is and ask instead of stopping it. Never copy another server's data.

## Logging in

Scripts and API calls log in with my dev login from `~/.config/ma-dev/login.env`. Never read or print that file, and never ask me to paste a login or token in chat.

1. If the file doesn't exist, create the template, then ask me to fill in my username and password between the quotes:
   ```bash
   [ -e ~/.config/ma-dev/login.env ] || (mkdir -p ~/.config/ma-dev && umask 077 && printf "MA_DEV_USERNAME=''\nMA_DEV_PASSWORD=''\n" > ~/.config/ma-dev/login.env)
   ```
2. Log in with a command that sources the file, so the values stay out of the transcript, and keep the token in `.claude/ma-token` with mode 600:
   ```bash
   (. ~/.config/ma-dev/login.env && umask 077 && jq -n --arg u "$MA_DEV_USERNAME" --arg p "$MA_DEV_PASSWORD" '{provider_id: "builtin", credentials: {username: $u, password: $p}}' | curl -sf -H 'Content-Type: application/json' -d @- http://localhost:<web port>/auth/login | jq -r .token > .claude/ma-token)
   ```
   Scripts read the token from `.claude/ma-token` and never print it. Log in again after a fresh copy or when the token stops working. If `.claude/ma-token` comes out empty, the login failed, so ask me to check the file.

## Frontend

Start it only when the task touches the frontend or I pass `frontend`. The built-in UI covers everything else.

1. In the frontend checkout or worktree for this task (default `~/projects/music-assistant/frontend`), run `pnpm install`, then start `pnpm dev` in the background.
2. Open the URL Vite prints, usually http://localhost:3000. When it asks for the server address, give `http://localhost:<web port>`.

## Debugging in VS Code

The server's `.vscode/launch.json` is tracked and runs on `~/.musicassistant`, so don't edit it. When I want to debug on the copy, or after `setup`, tell me to add `"--data-dir", "${workspaceFolder}/.claude/ma-data"` to the "Music Assistant: Server" arguments myself.

## Hand back

Say what's running, on which web, stream and Sendspin ports and data folder, and how to stop it. After `setup`, say what was prepared instead.
