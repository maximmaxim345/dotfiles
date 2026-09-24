# Commit Message Subagent

Analyze the staged diff and propose a commit message.

## Steps

1. Run `git diff --staged` to see the changes
2. List the changes in detail (files modified, what was added/removed)
3. Propose a commit message following the rules below

## Commit Type Rules

Pick from intent, not diff shape:

- `fix:` corrects wrong/broken behavior, even if mostly additions
- `feat:` adds a new capability the user can use
- `refactor:` restructures without behavior change
- `perf:` is a measurable speed/memory win
- `chore:` / `docs:` / `test:` cover non-code or scaffolding

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

Don't infer style from `git log -10` on the default branch. In
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

1. Measure the subject with a command instead of counting by eye: `printf %s 'fix: ...' | wc -c`. The count includes the `type:` prefix and any backticks.
2. If it exceeds 72, shorten and measure again. To shorten, move a function or method name to the body, drop words like "when", "before", "after", "in", and use shorter verbs (`drop` not `discard`, `fix` not `resolve`).
