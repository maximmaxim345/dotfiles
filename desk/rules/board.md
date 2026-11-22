## Board

`bin/board` serves the board at http://127.0.0.1:8765. It shows the backlog, a Done view, a page per goal, and the threads from `state/threads.json`, which `bin/board-threads` writes in each sweep and refresh. It leaves out threads whose item is done or dropped, and those whose item is paused unless they run or wait on me, since their cards show them. It keeps the desk's earlier `needsYou` whys while the thread waits, and adds `item` and `effort` to each entry:

```json
{
  "updated": "2026-10-21 09:00",
  "environment": "<environmentId from t3_environment_read>",
  "managers": {"<effort>": "<manager thread id>"},
  "needsYou": [{"thread": "<id>", "title": "...", "why": "push OK for #12", "pr": "<url or null>"}],
  "waiting": [],
  "snoozed": [{"thread": "<id>", "title": "...", "until": "2026-10-23 09:00", "pr": "<url or null>"}],
  "working": [],
  "failed": [],
  "unassigned": []
}
```

A snoozed thread goes only in `snoozed`, with its wake time in local time. A thread with an item whose last run failed or was interrupted goes in `failed`. The board adds items with `asks` to its Now tab itself and drops a `needsYou` entry for the same thread in their favor.

On the board I can capture notes (status `new`), comment on items, move items above or below the line of my Today list, set my minutes budget, mark items urgent, start, pause, finish (Done), drop or reopen items, archive an effort's finished items, add spaces, turn them on or off and move efforts between them (see "Spaces"), set blockers, change their effort or repo, hide Incoming entries (status dismissed) or snooze them until tomorrow or next week, apply or dismiss proposed project board changes, write in the chat of an Incoming entry or a proposed change, and set auto-start (see "Auto-start"). The server logs each action to `state/events.jsonl` for `bin/desk-wait`. It never launches anything itself.

The board listens only on 127.0.0.1 unless `board.json` names my Mac's Tailscale address (`{"tailnet": "100.x.y.z"}`). Then it also listens there after a restart (`launchctl kickstart -k gui/$(id -u)/local.desk-board`), and every request on that address needs the token in `state/board.token`. `bin/board --login-url` prints a link that sets the token as a cookie in the browser that opens it, once and within 10 minutes.
