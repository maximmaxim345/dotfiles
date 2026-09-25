---
name: implement
description: Build a feature or fix end to end in my workflow (branch, plan, implement, fresh-context review, handoff).
argument-hint: "<task description or issue URL>"
disable-model-invocation: true
---

Task: $ARGUMENTS

Nothing gets pushed during this skill. Shipping happens through `/open-pr` after my review.

## 1. Set up

- Read the repo's `CLAUDE.md` or `AGENTS.md` and its project rules file (see "Project rules" in my CLAUDE.md).
- If the task is an issue URL, read it with `gh issue view`.
- Fetch the base branch (the repo default unless the project rules say otherwise). If `origin` is my fork, sync it with upstream first.
- Locally, work in a worktree under `<repo>/.claude/worktrees/<slug>` unless the session already runs in one or I said `./`. In a cloud session (`CLAUDE_CODE_REMOTE` is `true`) the checkout is already isolated, so skip the worktree.
- Name the branch `<type>/<slug>` right away.

## 2. Plan

Read the code the change touches and the closest sibling code it should match. If the requirements are unclear, interview me first, using the `grilling` skill when it's available.

Then present a plan and wait for my approval:
- the files that change and where new state lives
- which existing code it follows
- the tests, each with the realistic regression it would catch
- what "done" means and how you'll verify it
- whether this should be more than one PR

For Music Assistant, Sendspin (except the spec), ESPHome, and OHF-Voice work, run the plan past ohf-sage before presenting it and include what it cites.

## 3. Implement

Commit as you go. A pure refactor gets its own commit before the behavior change. Run the project's lint, type checks, and tests, and fix failures you caused.

## 4. Review with fresh context

Launch these in parallel, passing the diff (`git diff <base>...HEAD`), the changed paths, and the approved plan, but not your own reasoning:
- A review subagent that checks correctness and audits the diff against my CLAUDE.md and the project rules: comments and docstrings, tests, simplicity, speculative or out-of-scope changes, dashes, and workarounds.
- ohf-sage, for the same projects as in step 2.

Label each finding as a user-visible bug, reachable but rare, or theoretical. Fix bugs and rule violations in separate commits and skip theoretical ones.

## 5. Hand over

End with:
- the absolute worktree path, the branch, and the commit range
- what you verified and how
- what I should test by hand
- findings you skipped or kept on purpose, one line each

Then stop and wait for my review. When I say to ship it, run `/open-pr`.
