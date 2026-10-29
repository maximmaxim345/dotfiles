# Music Assistant server

- Keep changes inside the provider. Ask before touching core controllers or models.
- Match the nearest sibling provider before adding something new: same error-handling scope, same guards, same helpers. Name constants instead of using magic numbers.
- Bump a provider dependency in its `manifest.json`. Pre-commit regenerates `requirements_all.txt` and `translations/en.json`, so never bypass it.
- In a worktree, run `scripts/setup.sh` before the first test or commit, and again after a rebase or merge that changes `pyproject.toml`, `requirements_all.txt` or a manifest pin. Never test or commit against the main checkout's venv or one borrowed from another worktree.
- `scripts/run-in-env.sh` runs the hooks in the main checkout's venv, which is usually behind `dev`, unless `UV_PROJECT_ENVIRONMENT` is set. So commit from the worktree root with `UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_NO_SYNC=1 git commit ...` in the same command. If a hook still fails only in files the branch doesn't touch after a fresh `scripts/setup.sh`, commit with `SKIP=<hook id>`, run that check on the changed files, and say so in the report. Never skip `gen_requirements_all` or `build_translations_source`.
- Don't reword existing strings only for terminology, since translations go through Lokalise.
- Use Music Assistant vocabulary in fields and text ("user", not "operator"), and keep model fields provider-neutral.
- Code against the released library API (for example `aiosendspin`), not a local checkout or name-matching stopgap.
- Before debugging frontend behavior, check which frontend version the server pins.
- When a test or reproduction needs real streaming providers, players, or library data, start the server with the `ma-dev` skill.
- Users read the docs at music-assistant/music-assistant.io (`~/projects/music-assistant/music-assistant.io`). When a change alters what users see, set up or configure, ask for a companion PR that updates them as "Companion PRs" in `~/desk/TASK.md` says, targeting the main or beta branch as its `CONTRIBUTING.md` says.
- PRs: fill the template as-is. Keep the "Related issue" header and leave it empty when there's no issue, never the placeholder. Tick exactly one "Types of changes" box (it picks the release-notes section), and the checklist boxes as `pr-guidelines.md` says. The title becomes the changelog line. Don't add `#` sections inside the description of a small PR.
- To measure playback offset with a mic (browsers, phones, native players, bad network), follow `~/projects/music-assistant/sendspin-sync-measure/AGENTS.md`.
