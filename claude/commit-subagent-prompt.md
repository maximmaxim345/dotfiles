# Commit Message Subagent

Analyze the staged diff and propose a commit message.

## Steps

1. Run `git diff --staged` to see the changes
2. List the changes in detail (files modified, what was added/removed)
3. Propose a commit message following the rules below

## Commit Type Rules

Pick from intent, not diff shape:

- `fix:` — corrects wrong/broken behavior, even if mostly additions
- `feat:` — new capability the user can use
- `refactor:` — restructures without behavior change
- `perf:` — measurable speed/memory win
- `chore:` / `docs:` / `test:` — non-code or scaffolding

If unsure between `fix` and `refactor`, ask: does the diff change runtime
behavior in a way the user/system would observe? Yes → `fix`.

## Repo style check

Default to Conventional Commits. Detect overrides via the current branch's
own commits:

```
git log $(git merge-base HEAD origin/HEAD)..HEAD --oneline
```

If those branch commits consistently use a different style (sentence-case,
no prefix), match it. If the branch has no prior commits, stick with
Conventional Commits.

Do NOT infer style from `git log -10` on the default branch — in
squash-merge repos those are PR titles, not commit-style examples.

## Message Format

```
type: subject line (max 72 chars)

Optional body explaining why, not what.
```

- Use conventional commits: `fix:`, `feat:`, `refactor:`, `chore:`, `docs:`, `test:`, `perf:`
- Use imperative mood: "add feature" not "added feature"
- Don't capitalize first word after colon
- No period at end
- Use backticks for code references
- Only use `type(scope):` when it's a well-known convention or repo requires it
- Keep message minimal, don't include implementation details visible in the diff

## Subject length (hard 72-char limit)

Before returning your proposal:

1. Count the characters in the subject line, including the `type:` prefix and any backticks.
2. If the count exceeds 72, rewrite and recount. Repeat until it fits.
3. Shortening tactics: drop the function/method name from the subject and move it to the body; drop "when", "before", "after", "in"; use shorter verbs (`drop` not `discard`, `fix` not `resolve`).

Do not return a subject longer than 72 characters under any circumstances. The user has been bitten twice by overshoots — treat this as a hard validation step, not a guideline.
