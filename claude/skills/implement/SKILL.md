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

Then present a plan. Open it with a numbered "Decide" list of the choices that are mine, most important first: your pick, one line why, and the alternatives as A, B, C. I answer "go" to accept every pick, or a number and a letter ("2B") to change one. With four or fewer choices and a popup tool in the session, ask them in one popup instead, with your pick first. Leave the list out when nothing is mine to decide. After it:
- the files that change and where new state lives
- which existing code it follows
- the simplest other design, such as doing it automatically without a new setting, and why it loses, checked against the code
- the tests, each with the realistic regression it would catch
- what "done" means and how you'll verify it
- whether this should be more than one PR
- each surface the project rules file lists for a feature, as changed or not needed
- when other code gets built against the change (models, commands, events, stored data, or anything another repo uses), the contract as one file kept out of git (add it to the file `git rev-parse --git-path info/exclude` names when nothing ignores it), linked in the plan: each model with its fields and types, each value with a descriptive name, and which side owns each piece of logic
- for a choice about where a feature lives in the UI or how a page is structured, an HTML mockup of your pick and of the closest alternative, with a screenshot of each that I can pass on
- when it adds a command or skill, how I'd use it: example calls, what happens without arguments, and each constraint I stated, in one line each

For Music Assistant, Sendspin (except the spec), ESPHome, and OHF-Voice work, run the plan past ohf-sage before presenting it when it involves a real design choice, and include what it cites. For a contract, also ask it what maintainers would object to.

Continue without waiting for my approval when all of these hold, and say so under the plan:
- the requirements are clear and you asked me nothing
- one approach clearly fits the existing code
- it's one PR, with no contract, protocol, public API or migration change
- nothing in it is expensive to undo and could reasonably go another way
- ohf-sage agrees, where it ran

Otherwise wait for my approval. In a desk task, `~/desk/TASK.md` "Plans" replaces this step's waiting rule.

## 3. Implement

Commit as you go. A pure refactor gets its own commit before the behavior change. Run the project's lint, type checks, and tests, and fix failures you caused.

Then test the change yourself the way I would, so I only do what needs me:
- Run the same scenario on the base branch and on the branch, both at default settings, and note every difference for the brief.
- For a Sendspin server change, test with a real client, `sendspin-cpp-cli` unless another test covers the change at least as well, and name what you used.
- When the change depends on a platform or Python version, run the relevant tests on those too, in a container when needed.
- For Music Assistant changes I would try in the app, start a server with the `ma-dev` skill and try the change there, on its demo Sendspin players when it involves players or playback. For frontend changes, also take screenshots of the changed screens as its "Frontend" part says.
- Ask me before testing on real speakers. For hand tests only I can do, set everything up first and give me numbered steps.
- For device or test rig sessions, plan the smallest set of runs that answers the question and name the result that ends testing. Ask before adding a run longer than about 10 minutes.

## 4. Review with fresh context

On a branch I call a prototype, skip this step and step 5, and hand over as "Before handing over" in my CLAUDE.md says.

Launch these in parallel, passing the diff (`git diff <base>...HEAD`), the changed paths, and the approved plan, but not your own reasoning:
- A review subagent that checks correctness, audits the diff as "Before handing over" in my CLAUDE.md says and against the project rules, and reads it as the `review-brief` skill's "Critical pass" says.
- ohf-sage, for the projects listed in step 2.

Label each finding as a user-visible bug, reachable but rare, or theoretical. Fix bugs and rule violations, each in a `git commit --fixup` of the commit it fixes, and skip theoretical ones. Note what you fixed and what you kept on purpose, with the reason, for the brief. Run a second round only to check those fixes, and no third. A finding that widens the change is an extra finding, not a fix.

When the item's start note asks for a second opinion, run it now as the `second-opinion` skill says for a start note, and treat its findings the same way.

## 5. Hand over

Ask for the companion PRs the change needs, such as a docs update, as "Companion PRs" in `~/desk/TASK.md` says. Then run the `review-brief` skill. Its "Critical pass" starts from what step 4 fixed and kept.

When the item's start note allows a draft PR and nothing blocks shipping, run `/open-pr` before the brief, in `draft` mode, or in `babysit` mode when the note says so, with no automatic review unless the note names one. The note is the go-ahead its step 6 asks for, once, for this branch. Put the PR's URL in the first line of the brief. A PR that changes docs or spec text still waits for my wording review.

Otherwise, when nothing blocks shipping, draft the PR in the same reply as `/open-pr` steps 1 to 6 say, without pushing. When something does, such as a decision or a hand test that blocks, end with that instead and draft the PR once it's resolved. Stop and wait for my review. Make fixes from my review as `--fixup` commits too, and post the updated PR draft with them. When I say to push or ship it, run `/open-pr`.
