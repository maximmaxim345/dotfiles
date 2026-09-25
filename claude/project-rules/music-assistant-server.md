# Music Assistant server

- Keep changes inside the provider. Ask before touching core controllers or models.
- Match the nearest sibling provider before adding something new: same error-handling scope, same guards, same helpers. Name constants instead of using magic numbers.
- Bump a provider dependency in its `manifest.json`. Pre-commit regenerates `requirements_all.txt` and `translations/en.json`, so never bypass it.
- Don't reword existing strings only for terminology, since translations go through Lokalise.
- Use Music Assistant vocabulary in fields and text ("user", not "operator"), and keep model fields provider-neutral.
- Code against the released library API (for example `aiosendspin`), not a local checkout or name-matching stopgap.
- Before debugging frontend behavior, check which frontend version the server pins.
- PRs: fill the template as-is. Keep the "Related issue" header and leave it empty when there's no issue, never the placeholder. Tick exactly one "Types of changes" box (it picks the release-notes section) and the AI policy box. The title becomes the changelog line.
