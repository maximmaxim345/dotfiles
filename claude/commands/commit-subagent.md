Create a commit following @~/.claude/commit-guidelines.md.

Delegate the commit-message proposal to a haiku subagent using `@~/.claude/commit-subagent-prompt.md`. Workflow:

1. If `git diff --staged` is empty, stage with `git add -A`.
2. Launch a haiku subagent with the prompt at `@~/.claude/commit-subagent-prompt.md`. Pass any short context that helps the subagent understand the change set (e.g. one-line summary of what was edited and why).
3. Review the subagent's output. Verify the change list against the actual diff. You may adjust wording or commit type if the subagent misread the diff. Re-check that the subject is at most 72 characters; if it overshoots, tighten before committing.
4. Commit with `git commit -m "..."`.

For the inline (no-subagent) variant use `/commit`.
