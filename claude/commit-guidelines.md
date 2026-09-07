# Commit Message Guidelines

## Before Committing

The user may have modified files since your last interaction. Base the commit only on the actual diff, not conversation context.

1. If `git diff --staged` is empty, stage changes with `git add -A`
2. Run `git diff --staged` and read it. Verify your assumptions about the change set against the actual diff
3. Compose a message following the rules below
4. Commit with `git commit -m "..."`

The `commit-subagent` and `commit-split-subagent` skills delegate step 3 to a haiku subagent via `@~/.claude/commit-subagent-prompt.md`. The plain `commit` and `commit-split` skills compose the message inline.

## Format

Default: Conventional Commits. Override only if the current branch's own
commits use a different style.

```
type: subject line (max 72 chars)

Optional body explaining why, not what.
```

Use conventional commits: `fix:`, `feat:`, `refactor:`, `chore:`, `docs:`, `test:`, `perf:`

### Detecting repo style

Read commits unique to the current branch:

```
git log $(git merge-base HEAD origin/HEAD)..HEAD --oneline
```

- If the branch has prior commits and they consistently use a different style
  (sentence-case, no prefix, etc.), match that style.
- If the branch has no prior commits, default to Conventional Commits.
- Do NOT use `git log -10` on the default branch to detect style. In
  squash-merge repos, those entries are PR titles, not commit-style examples.

## Subject Line

- Keep under 72 characters (GitHub's limit)
- Use imperative mood: "add feature" not "added feature"
- Don't capitalize first word after colon
- No period at end
- Use backticks for code references: ``fix: handle `None` in parser``

## Scope

Only use `type(scope):` when:
- It's a well-known convention (e.g., `chore(deps):`)
- Repo style guide requires it

Otherwise just use `type:` without scope.

## Body

Skip unless the diff doesn't explain the "why". The reviewer has both the message and the code.

When needed:
- One blank line after subject
- Wrap at 72 characters
- Explain motivation, not mechanics
- Don't repeat what code comments already say

## Examples

Good:
```
refactor: move validation to its own module
```

```
fix: handle empty input in `parse_config`
```

```
feat: add dark mode toggle

Users requested this in #234. Defaulting to system preference
since that matches platform conventions.
```

```
refactor: rename `UserData` to `PersistentUserData`

The old name was ambiguous now that sessions track
non-persistent user state separately.
```

Bad:
- `fix: Fixed the bug` (past tense, vague)
- `Update code` (no type, vague)
- `feat: Add new feature for handling the edge case where...` (too long)
- Body that restates what the diff shows

## Don't

- Add body just to have one
- Explain what changed (the diff shows that)
- Use past tense
- Exceed 72 characters in subject
- Reference PRs, issues, or tickets in the message
