---
name: ma-dev
description: Start a Music Assistant dev server, and the frontend when needed, on a copy of my configured data folder with working streaming providers and players. Use when a Music Assistant test or reproduction needs real providers, players, or library data.
argument-hint: "[setup|frontend]"
---

Start a Music Assistant server from the current server checkout or worktree, on a copy of `~/.musicassistant`. That folder is logged in to my streaming providers, so the copy works without setup. Never point a server at `~/.musicassistant` itself.

## Backend

Run these from the server checkout or worktree for this task (default `~/projects/music-assistant/server`):

1. Check that port 8095 is free with `lsof -nP -iTCP:8095 -sTCP:LISTEN`. If another server holds it, tell me instead of stopping it or copying its data.
2. If `.venv` is missing, run `scripts/setup.sh`.
3. If `.claude/ma-data` is missing, copy the data folder without its cache, logs, and backups. The repo's `.gitignore` covers `.claude/`, so the copy and its tokens stay out of git.
   ```bash
   rsync -a --exclude .cache --exclude 'musicassistant.log*' --exclude '*.backup' ~/.musicassistant/ .claude/ma-data/
   ```
   Reuse an existing copy so its state survives restarts. Delete it to start fresh.
4. Start the server in the background. `MASS_APP_VARS_FILE` provides the bundled provider credentials.
   ```bash
   PYTHONDEVMODE=1 MASS_APP_VARS_FILE="$HOME/projects/music-assistant/appvars/app_vars.json" .venv/bin/python -m music_assistant --log-level debug --data-dir .claude/ma-data
   ```

The server's built-in UI is at http://localhost:8095.

With `setup`, do steps 1 to 3 and start nothing, not even the frontend, then give me the VS Code line below so I can start it with F5.

## Frontend

Start it only when the task touches the frontend or I pass `frontend`. The built-in UI covers everything else.

1. In the frontend checkout or worktree for this task (default `~/projects/music-assistant/frontend`), run `pnpm install`, then start `pnpm dev` in the background.
2. Open the URL Vite prints, usually http://localhost:3000. When it asks for the server address, give `http://localhost:8095`.

## Debugging in VS Code

The server's `.vscode/launch.json` is tracked and runs on `~/.musicassistant`, so don't edit it. When I want to debug on the copy, or after `setup`, tell me to add `"--data-dir", "${workspaceFolder}/.claude/ma-data"` to the "Music Assistant: Server" arguments myself.

## Hand back

Say what's running, on which ports and data folder, and how to stop it. After `setup`, say what was prepared instead.
