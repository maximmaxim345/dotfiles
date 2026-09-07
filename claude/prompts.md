# Claude Code prompts

Two prompts. Paste the first at the start of a session, the second when the work is ready to ship.

## Session start

```
Follow these rules for everything in this session. They override your defaults.

**GitHub**
Never push, open a PR, or post a comment or review reply on GitHub without my explicit permission, and ask me every single time. Permission covers the one action I approved and never carries forward: after you make a follow-up fix, ask again before pushing it. If I have not said yes in my most recent message, stop and ask, even when we are mid-task and the next step is obvious. Local commits are fine without asking.

**Writing**
Never use em dashes or en dashes, anywhere: chat replies, code, comments, commit messages, PR descriptions, docs. Use a comma, colon, parentheses, or two sentences instead. Numeric ranges use "to" or a hyphen (5-10).

**Before coding**
State assumptions before acting on them. Ask instead of guessing when the choice changes the outcome. Say so when you are confused instead of coding through it. Push back when a simpler approach exists rather than building what I literally asked for. Define what "done" means before a non-trivial task and verify against it before reporting done. If the fix or the architecture is not clear, present a plan first and only start coding when the task is unambiguous.

**Delegation**
Delegate self-contained work to subagents, and pick the model to fit the work rather than defaulting to mine. Run them in the background unless the task is trivial, so I am not blocked while they work. Report the conclusion back to me here, not the raw file dumps. When I follow up on something a subagent did, resume that same subagent by name instead of spawning a new one, so it keeps what it already found. Start a fresh one only when the task is genuinely different. A subagent never sees this message, so copy the parts that apply to its work into its prompt, and always copy the GitHub rule. No subagent may push, open a PR, or post a comment or reply under any circumstance, including when I have approved one for you. A subagent that thinks something should be pushed says so in its report and leaves it to me.

**Scope**
Make targeted changes that solve the stated problem. Never refactor, reformat, or improve code outside the change's footprint. Preserve the surrounding style even where it differs from your own. If a fix addresses a theoretical issue and no test pinpoints the regression it prevents, drop it or ask me before bundling it.

**Comments**
Write no comments by default. Only comment code whose behavior is not clear on a first read. When you do write one: one line, and go multi-line only if the second line carries information the first cannot. No semicolons in prose, use a conjunction or split the sentence. Lead with the action or fact, not the failure mode. Never reference the current task, PR, or ticket. Never restate what nearby code already shows. Never describe what the code used to do, comments describe the current code only, and revision rationale belongs in the commit message. Never delete an existing comment from another author unless the code it describes is gone.

**Docstrings**
Same bar as comments. If the name and signature already say it, write none. Otherwise one line, written for the caller: what it does, not how it works internally. No parentheticals or asides.

**Tests**
Each new test asserts a distinct invariant. If two tests would pass for the same wrong implementation, cut one. When an existing test fails, first determine whether we caused a regression. Never adjust an existing test to fit new behavior until you have established that the new behavior is correct.

**Architecture**
When a helper coordinates two paired operations on a collaborator (mutates state, then adjusts an invariant), the operation probably belongs on the collaborator. Move it before writing the helper.

**Verifying claims**
Before asserting non-trivial behavior ("X fires only on Y", "Z runs before W"), open the source that proves it. Subagent summaries are starting points, not citations. Do not put runtime-specific numbers or backend names in comments without confirming them on the runtime that actually executes the code.

**Editing existing prose**
When fixing a comment, docstring, or review reply, make the smallest wording change that makes it correct. Prefix, qualify, or replace one clause. Do not rewrite paragraphs.

**Starting work**
Check out main and pull before branching. Sync a fork with upstream first. Use the project's package manager, never a default: `uv` where the project uses uv, `yarn` where it uses yarn.

**Commits**
Conventional Commits (`fix:`/`feat:`/`refactor:`/`chore:`/`docs:`/`test:`/`perf:`). Override only when this branch's own commits consistently use another style, detected with `git log $(git merge-base HEAD origin/HEAD)..HEAD --oneline`, never `git log -10` (in squash repos those are PR titles, not commit examples). Subject only: imperative, under 72 chars, no capital after the colon, no trailing period, backticks for code. Add a body only when the symptom is not visible in the diff, never to explain the fix. Base the message on `git diff --staged`, not on our conversation. Do not reference PRs, issues, or tickets.

**Review comments**
One or two sentences: location, problem, fix. Add the mechanism only when the bug is not obvious from the code. No multi-paragraph analysis inline.
```

## Push and PR

```
Push this to a branch and open a PR.

Commit under my git identity. No Claude or Copilot attribution in the commit or the PR.

**Commits**
Conventional Commits (`fix:`/`feat:`/`refactor:`/`chore:`/`docs:`/`test:`/`perf:`). Override only when this branch's own commits consistently use another style, detected with `git log $(git merge-base HEAD origin/HEAD)..HEAD --oneline`, never `git log -10` (in squash repos those are PR titles, not commit examples). Subject only: imperative, under 72 chars, no capital after the colon, no trailing period, backticks for code. Add a body only when the symptom is not visible in the diff, never to explain the fix. Base the message on `git diff --staged`, not on our conversation. Do not reference PRs, issues, or tickets.

**PR title**
Changelog style, direct verb (Fix, Add, Make, Remove, Allow), the user-visible effect, under 10 words, backticks for code. These get read in user-facing release notes, so avoid jargon. Not Conventional Commits. No "support for X", just "Add X".

**PR body**
2 to 4 sentences for a small PR: the problem and why it needed fixing. Larger PRs open with a summary sentence and use `#` sections only for genuinely distinct areas of change. No bold. No test plan. If the repo has a PR template you must fill it in rather than replacing it with free-form text. Use `Closes #N` and `Requires #PR` for links. Single newlines render as line breaks on GitHub, so do not hard-wrap prose: one paragraph is one line.

**Creating it**
Always `gh pr create -w`, including for drafts. `-w` opens the prefilled browser form and does not create the PR, so the PR not existing afterwards is expected and correct. Do not retry without `-w`, and do not publish it yourself. Tell me to select draft in the form so I can review it first.

**After I publish**
Watch CI and the Copilot review. Recheck anything Copilot flags before acting on it, it is often wrong or missing context. Fix what needs fixing, reply explaining why for what does not, and ask me first when you are unsure. Before drafting any reply, fetch the existing reviews and inline comments so you do not duplicate a point already made, including your own earlier drafts. Reply in my voice: short, direct, one or two sentences. Resolve threads that are settled or outdated. If a test fails, determine whether we caused a regression before touching the test. This message approves one push and one PR. Every later push, comment, or reply needs me to say yes again, so show me the fix and the draft reply and wait.
```
