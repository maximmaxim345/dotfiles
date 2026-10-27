---
name: implement
description: Build a feature or fix end to end in my workflow (branch, plan, implement, fresh-context review, handoff). Use for code changes in a repo listed under "Project rules" in my CLAUDE.md, even without /implement.
argument-hint: "<task description or issue URL>"
---

Task: $ARGUMENTS

Nothing gets pushed during this skill. Shipping happens through `/open-pr` after my review.

## 1. Set up

- Read the repo's `CLAUDE.md` or `AGENTS.md` and its project rules file (see "Project rules" in my CLAUDE.md).
- If the task is an issue URL, read it with `gh issue view`.
- For a bug, confirm it's real before planning a fix.
- Fetch the base branch (the repo default unless the project rules say otherwise). If `origin` is my fork, sync it with upstream first.
- Locally, work in a worktree under `<repo>/.claude/worktrees/<slug>` unless the session already runs in one or I said `./`. In a cloud session (`CLAUDE_CODE_REMOTE` is `true`) the checkout is already isolated, so skip the worktree.
- Name the branch `<type>/<slug>` right away, except in a cloud session, which keeps its assigned branch.

## 2. Plan

Read the code the change touches and the closest sibling code it should match. If the requirements are unclear, interview me first, using the `grilling` skill when it's available.

Then present a plan:
- the files that change and where new state lives
- which existing code it follows
- the tests, each with the realistic regression it would catch
- what "done" means and how you'll verify it
- whether this should be more than one PR

For Music Assistant, Sendspin (except the spec), ESPHome, and OHF-Voice work, run the plan past ohf-sage before presenting it when it involves a real design choice, and include what it cites.

Continue without waiting for my approval when all of these hold, and say so under the plan:
- the requirements are clear and you asked me nothing
- one approach clearly fits the existing code
- it's one PR, with no protocol, public API or migration change
- ohf-sage agrees, where it ran

Otherwise wait for my approval. In a desk task, `~/desk/TASK.md` "Plans" replaces this step's waiting rule.

## 3. Implement

Commit as you go. A pure refactor gets its own commit before the behavior change. Run the project's lint, type checks, and tests, and fix failures you caused.

## 4. Review with fresh context

Launch these in parallel, passing the diff (`git diff <base>...HEAD`), the changed paths, and the approved plan, but not your own reasoning:
- A review subagent that checks correctness, audits the diff as "Before handing over" in my CLAUDE.md says and against the project rules, and reads it as the `review-brief` skill's "Critical pass" says.
- ohf-sage, for the projects listed in step 2.

Label each finding as a user-visible bug, reachable but rare, or theoretical. Fix bugs and rule violations, each in a `git commit --fixup` of the commit it fixes, and skip theoretical ones. Note what you fixed and what you kept on purpose, with the reason, for the brief.

## 5. Hand over

Run the `review-brief` skill. In its "Before I read" part, also say what you verified and how, and what I should test by hand. Its "Critical pass" starts from what step 4 fixed and kept.

Then, in the same reply, draft the PR as `/open-pr` steps 1 to 6 say, without pushing. Stop and wait for my review. Make fixes from my review as `--fixup` commits too, and post the updated PR draft with them. When I say to push or ship it, run `/open-pr`.
