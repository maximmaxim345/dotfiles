# sendspin-js

- Forward every new `SendspinPlayerConfig` option through the allowlist in `src/index.ts`.
- In a fresh worktree, run `yarn build` once before `yarn dev-server`, which needs `src/silent-audio.generated.ts`.
- `productName` has no default since 4.0.0. Music Assistant must pass "Web Browser" or web player detection breaks.
- Describe behavior against the spec in errors, README, and comments. Never name another implementation (like `aiosendspin`). When code handles another implementation's deviation from the spec, call it a non-compliant server.
- Keep experimental work in `wip:` commits on separate branches.
- PRs: fill `.github/PULL_REQUEST_TEMPLATE.md` and tick exactly one "Types of changes" box, or the Verify check fails.
- To measure playback offset with a mic (browsers, phones, native players, bad network), follow `~/projects/music-assistant/sendspin-sync-measure/AGENTS.md`.
- Always look closely, however small the change: `src/types.ts` and the option allowlist in `src/index.ts` (the public API), the protocol and time sync code in `src/core/`, `src/sync-delay.ts`, and audio scheduling in `src/audio/`.
- A feature reaches these surfaces, and the plan names each as changed or not needed: the library, its README, the Music Assistant frontend that passes the options, and Sendspin/spec when the wire changes.
