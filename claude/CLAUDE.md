# Global Preferences

## Pushing and publishing

Never push, open a PR, or post a comment or review reply on GitHub without
explicit permission, and ask every single time. Permission covers the one
action that was approved and never carries forward: after a follow-up fix,
ask again before pushing it. If the user hasn't said yes in their most recent
message, stop and ask, even mid-task when the next step is obvious. Local
commits are fine without asking.

Marking a PR draft or ready, editing a description, resolving threads, and
moving board cards count as posting too. On someone else's PR, push to its head
branch (`headRepositoryOwner` and `headRefName` from `gh pr view`), never a new
branch on origin, and show me the exact push command first.

## Before coding

State assumptions before acting on them. Ask instead of guessing when a
choice changes the outcome. Push back when a simpler approach exists rather
than building what was literally asked. Stop and say so when confused instead
of coding through it.

A question asking for information or an opinion ("why does X happen?",
"should we do Y?") is not a request to act. Answer it and stop. A request
phrased politely as a question ("can you fix X?") is a request.

When the fix or the architecture isn't clear, present a plan first and work
out the approach. Only start coding immediately when the task is unambiguous.

## Success criteria

Define what "done" looks like before starting a non-trivial task, then verify
against it before reporting done. Concrete criteria (a passing test, a
specific output) are what let a task run to completion without checking in at
every step.

## Project rules

Before working in one of these repos (matched by the `origin` remote, or by
its upstream when `origin` is my fork), read its
file in `~/.claude/project-rules/`:
- `music-assistant/server`: `music-assistant-server.md`
- `music-assistant/frontend`: `music-assistant-frontend.md`
- `Sendspin/aiosendspin`: `aiosendspin.md`
- `Sendspin/sendspin-js`: `sendspin-js.md`
- `Sendspin/spec`: `sendspin-spec.md`

## Starting work

Start from an up-to-date base: check out the main branch and pull before
branching. If the repo is a fork, sync it with upstream first.

Use the project's package manager, don't reach for a default. When a project
uses `uv`, set up its environment with `uv`, not pip or a manual venv. When it
uses `yarn`, run `yarn`, not npm.

## Delegating to subagents

Delegate only large, self-contained work (a wide multi-file investigation, an
independent parallel track), since each subagent re-reads context and reports
back. Pick the model to fit the work and run it in the background. Report the
conclusion, not the raw file dumps. For a follow-up on work a subagent already
did, resume that subagent by name instead of spawning a new one, so it keeps what it
found. Start a fresh one only when the task is different.

Use ohf-sage for Music Assistant, Sendspin, ESPHome, and OHF-Voice
implementation work, when settling a plan and before handing work over. Do
small reviews and Sendspin spec text yourself, and use ohf-sage for those only
when I ask.

Subagents don't inherit anything pasted into the session, so copy the rules
that apply to their work into their prompt. No subagent may push, open a PR,
or post a comment or reply under any circumstance, including when the user
approved one for the main session. A subagent that thinks something should be
pushed says so in its report and leaves it to the user.

## Dashes

NEVER use em dashes (—) or en dashes (–). Applies everywhere: chat replies,
code comments, commit messages, PR descriptions, docs. Use a comma, colon,
parentheses, or two sentences instead. For numeric ranges write "to" or a
hyphen (5-10), not an en dash.

## Comment style

Write no comments by default. Only comment code whose behavior isn't clear on
a first read. When a comment is warranted:
- Prefer a single line. Multi-line only when the WHY needs it.
- No semicolons in prose. Use plain conjunctions or split into a separate sentence.
  - Avoid: `# Stale source position; would replay wrong after silence.`
  - Prefer: `# Drop buffered output with stale source positions.`
- Lead with the action/fact, not the failure mode. Reader can infer the failure
  if the action is named precisely.
- Don't reference the current PR, ticket, or task. Don't restate what nearby code
  already shows.
- Explain WHY about the code itself (its current behavior, design, or a non-obvious
  constraint), not WHY it changed from a previous revision. Revision rationale
  belongs in the commit message, not a code comment.
- Don't delete an existing comment from another author unless the code it
  describes is gone.

## Docstrings

Same treatment as comments. If the helper name + signature already says it,
write no docstring. Otherwise single line. No parentheticals or asides.

## Commit messages

Default to Conventional Commits (`fix:`/`feat:`/`refactor:`/`chore:`/`docs:`/
`test:`/`perf:`). Override only when the current branch already has its own
commits AND they consistently use another style: detect with
`git log $(git merge-base HEAD origin/HEAD)..HEAD --oneline`, not `git log -10`
(in squash repos those entries are PR titles, not commit-style examples). No
prior commits on the branch means Conventional Commits. No `type(scope):`
unless it's a well-known convention (`chore(deps):`) or the repo requires it.

Subject-only is the default: imperative, under 72 chars, no capital after the
colon, no trailing period, backticks for code. Add a body only when the SYMPTOM
isn't visible from the diff, never to explain the fix. Base the message on
`git diff --staged`, not the conversation, and stage with `git add -A` only if
nothing is staged. Don't reference PRs, issues, or tickets in a commit message.

No Claude attribution or session links in commits or PR descriptions.

## Branches and history

Name branches `<type>/<slug>` with a Conventional Commits type, and rename
auto-generated worktree branches before the first push.

A pure refactor goes in its own commit before the behavior change. While I'm
reviewing, add each fix as its own commit. Before the PR, fold fixups into the
commits they fix, but only my unpushed ones. Never rewrite published commits or
commits by someone else. Debug or local-only code goes in `wip:` commits at the
top of the branch.

## Worktrees and handoff

Create worktrees under `<repo>/.claude/worktrees/<name>`, never in `/tmp` or a
scratchpad. When I say `./`, work in the current checkout. When handing work
over for review, end with the absolute folder path, the branch, and the commit
range.

## Before handing over

Before telling me work is ready for review, have a subagent that didn't write
the code audit the diff against this file: comments and docstrings, tests,
dashes and semicolons, speculative or out-of-scope changes, and workarounds.
For Music Assistant, Sendspin (not the spec), ESPHome, and OHF-Voice, also
have ohf-sage review the diff. Fix what they find and tell me what you kept on
purpose. Skip this only when the diff changes no behavior and touches no tests
or docstrings.

## Verifying behavior claims

Before asserting non-trivial behavior ("X fires only on Y", "Z is called
before W"), open the source path that proves it. Subagent summaries are
starting points, not citations.

When summarizing a set of things (sessions, commits, a diff), say how much of it
you actually read. Before a review or compliance check, fetch the base branch
and the spec, and name the commit you compared against.

Don't bake runtime-specific magnitudes or backend names into comments
without confirming on the runtime that executes the code. Generic
mechanism wording survives backend swaps; specifics don't.

## Speculative fixes

If a fix addresses a theoretical issue and no test pinpoints the
regression it prevents, default to dropping it, or ask before bundling.
Belt-and-suspenders patches inflate the diff, outlive the bug, and hide
which change actually fixed the user's symptom.

When acting on review findings (mine, Copilot's, ohf-sage's), first label each
as a user-visible bug, reachable but rare, or theoretical. Skip theoretical
ones by default and say so.

Same goes for scope. Make targeted changes that solve the stated problem.
Don't refactor, reformat, or "improve" code outside the change's footprint.
Preserve the surrounding style even where it differs from your own.

## Tests

Each new test asserts a distinct invariant. If two tests would pass for
the same wrong implementation, one is redundant. Cut it before commit.

Add a test only when it would catch a realistic regression. No tests that
depend on the CI environment (like the installed ffmpeg build), and no helpers
extracted only to make something testable.

When an existing test fails, first work out whether we caused a regression.
Don't adjust an existing test to fit the new reality until the new behavior
is established as correct.

## Refactor smell

When a helper coordinates two paired ops on a collaborator (e.g. mutates
state and adjusts an invariant), suspect the operation belongs ON the
collaborator. Move it before writing the helper.

## Simplicity

Inline single-use helpers unless the name carries a concept. No casts, unit
conversions, or local imports the surrounding code doesn't need. Check for an
existing library or framework primitive before adding polling, throttling, or
a new abstraction. When a solution works around the framework (polling,
heuristics, private access), say so and whether it would pass maintainer review.

## Editing existing prose

When fixing existing comments, docstrings, or review replies, prefer the
smallest wording change that makes it correct. Prefix, qualify, or replace
one clause, don't rewrite paragraphs. Large rewrites on doc-only fixes
read as scope creep and bloat the diff.

## GitHub markdown

Single newlines render as line breaks. Don't hard-wrap prose mid-sentence in
PR descriptions, issues, or comments. Breaking the line between sentences is fine.

## Writing style

Use this style for anything written for other people under my name, such as
PR titles and descriptions, review comments, issue comments, and replies.
Match the voice in these examples:
@~/.claude/writing-examples.md

Also:
- No bold.
- Links go in a list under a short lead-in ("Superseded by:", "Related:"),
  one per line.
- State opinions in first person with the reason ("I think X, since Y").
- Don't use "genuinely", "notably", or "essentially".
- Use plain, common words and the host project's vocabulary. If a word needs
  defining, pick another word.
- First drafts of comments and replies for other people are one or two
  sentences. PR descriptions follow the PR length rules. Show one version.
- When I hand you my draft, keep its structure and wording and only fix what's
  wrong.
- Keep a rule's reason out of the rule itself (spec text, option
  descriptions). The reason goes in the PR description.
- When I correct wording in one place, apply it everywhere it fits and list
  where.

## PRs

Title: changelog-style, direct verb ("Fix...", "Add..."), user-visible effect,
under 10 words, backticks for code. Not Conventional Commits, no "support for
X" (just "Add X").

Body: 2-4 sentences for small PRs (problem and fix). Larger PRs open with a
summary sentence, with `#` sections only for distinct areas. No bold,
no test-plan section unless asked. If the repo has a PR template, use it.
Use `Closes #N` / `Requires #PR` for links, unless the template has a
related-issues field: then fill that the way the template shows.

Always create with `gh pr create -w` (opens the prefilled browser form, even
for drafts: tell the user to pick draft in the form). The only exceptions are in
`/open-pr`: `draft` mode, and its fallback when no browser is available. `-w` does
NOT create the PR, so a missing PR afterward is expected: don't retry without
`-w`, don't publish it yourself.

## PR review workflow

Before drafting review comments, fetch existing reviews and inline comments
on the PR (Copilot, other reviewers, your own drafts). Don't create a new
comment that duplicates or partially overlaps an existing one, even your
own drafts from a prior PR version. Map proposed feedback against what's
already there, drop duplicates, only add uncovered points. State
coverage explicitly when reporting back.

## After a PR is published

Watch CI and the Copilot review. Recheck anything Copilot flags before acting
on it, it's often wrong or missing context. Fix what needs fixing, reply
explaining why for what doesn't, and ask when unsure. Reply in my voice (see
"Writing style"): short, direct, one or two sentences. Ask before resolving threads that are settled
or outdated.

## Review comment style

Default to one or two sentences: location + problem + fix. Add the
mechanism only when the bug isn't obvious from the code. No multi-paragraph
analysis in inline comments. That belongs in the PR description or a
separate discussion thread.
