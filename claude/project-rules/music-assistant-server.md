# Music Assistant server

- Keep changes inside the provider. Ask before touching core controllers or models.
- Match the nearest sibling provider before adding something new: same error-handling scope, same guards, same helpers. Name constants instead of using magic numbers.
- Bump a provider dependency in its `manifest.json`. Pre-commit regenerates `requirements_all.txt` and `translations/en.json`, so never bypass it.
- In a worktree, run `scripts/setup.sh` before the first test or commit, and again after a rebase or merge that changes `pyproject.toml`, `requirements_all.txt` or a manifest pin. Never test or commit against the main checkout's venv or one borrowed from another worktree.
- `scripts/run-in-env.sh` runs the hooks in the main checkout's venv, which is usually behind `dev`, unless `UV_PROJECT_ENVIRONMENT` is set. So commit from the worktree root with `UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_NO_SYNC=1 git commit ...` in the same command. If a hook still fails only in files the branch doesn't touch after a fresh `scripts/setup.sh`, commit with `SKIP=<hook id>`, run that check on the changed files, and say so in the report. Never skip `gen_requirements_all` or `build_translations_source`.
- Don't reword existing strings only for terminology, since translations go through Lokalise.
- Use Music Assistant vocabulary in fields and text ("user", not "operator"), and keep model fields provider-neutral.
- Code against the released library API (for example `aiosendspin`), not a local checkout or name-matching stopgap.
- The dependency review check clears with the `dependencies-reviewed` label. Ask before adding it, and never post `/approve-dependencies`.
- A run with the C++ sendspin-cli (`~/projects/music-assistant/sendspin-cpp-cli`) counts as a real device test, also when Bot-MArley asks about hardware testing.
- Before drafting a bug-fix PR, search music-assistant/support, open and closed, and read the matching reports in full, logs included. List matches in chat with full URLs, and leave them out of the PR unless I say to add them.
- Before debugging frontend behavior, check which frontend version the server pins.
- When a test or reproduction needs real streaming providers, players, or library data, start the server with the `ma-dev` skill.
- Users read the docs at music-assistant/music-assistant.io (`~/projects/music-assistant/music-assistant.io`). When a change alters what users see, set up or configure, ask for a companion PR that updates them as "Companion PRs" in `~/desk/TASK.md` says, targeting the main or beta branch as its `CONTRIBUTING.md` says.
- PRs: fill the template as-is. Keep the "Related issue" header and leave it empty when there's no issue, never the placeholder. Tick exactly one "Types of changes" box (it picks the release-notes section), and the checklist boxes as `pr-guidelines.md` says. The title becomes the changelog line. Don't add `#` sections inside the description of a small PR.
- To measure playback offset with a mic (browsers, phones, native players, bad network), follow `~/projects/music-assistant/sendspin-sync-measure/AGENTS.md`.

## Models, commands and events

These cover the shared models (music-assistant/models) and the commands and events the frontend and the app read. A reviewer checks every bullet, including anything kept on purpose.

- Every field, enum value, event and command a change adds or touches is set by the server and read by at least one client. Cut what isn't. Before cutting a field as unread, read the code that consumes the object, not only a search for its name.
- Every value of such a field is one the shipping server can produce. Trace each bool, optional and enum field to where the server sets it. A value only old or prototype data can hold makes the field dead.
- A name says what the thing is, and one word names one concept across names, values and texts.
- No duplicate models. Reuse the model that already groups the fields, and when two models look alike, their docstrings say how they differ.
- No field that repeats another field or a value a client can derive.
- A known shape gets a type: no `dict[str, Any]` and no magic keys mixed into a map.
- Use a bool, not a two-value enum whose names add nothing (`stop: user | timeout` becomes `timed_out: bool`).
- A field or value too niche for the shared model stays out of it, such as a value only one mode of one feature uses.
- Something only a later PR uses ships with that PR.
- A deprecated field is marked the same way everywhere, with the same removal note.
- Every event documents its `object_id` and data.
- Every comment and docstring matches what the code does today. Open the code each one describes, also in another repo, instead of checking only its style.
- Follow upstream precedent: where upstream adds the same kind of thing without a workaround for old clients, do the same (a new filter type joins the filters union as is). Don't add a compatibility shim on save when the old fields still parse and a one-time migration covers stored data.
