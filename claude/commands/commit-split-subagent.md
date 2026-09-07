Split uncommitted changes into multiple logical commits using `git add -p`, with each commit message proposed by a haiku subagent.

Follow the workflow in `/commit-split` (analyze, group, plan, confirm, execute), with one change to step 4: after staging each group's hunks, do not write the commit message inline. Instead:

1. Run `git diff --staged` to confirm the staged hunks match the planned group.
2. Launch a haiku subagent with `@~/.claude/commit-subagent-prompt.md`. Pass a one-line summary of what this commit is intended to capture so the subagent has the framing.
3. Verify the proposal: change list matches the staged diff, subject ≤72 chars. Tighten if needed.
4. Commit with `git commit -m "..."`.

For the inline (no-subagent) variant use `/commit-split`.
