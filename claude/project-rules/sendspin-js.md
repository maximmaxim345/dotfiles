# sendspin-js

- Forward every new `SendspinPlayerConfig` option through the allowlist in `src/index.ts`.
- In a fresh worktree, run `yarn build` once before `yarn dev-server`, which needs `src/silent-audio.generated.ts`.
- `productName` has no default since 4.0.0. Music Assistant must pass "Web Browser" or web player detection breaks.
- Describe behavior against the spec in errors, README, and comments. Never name another implementation (like `aiosendspin`). When code handles another implementation's deviation from the spec, call it a non-compliant server.
- Keep experimental work in `wip:` commits on separate branches.
