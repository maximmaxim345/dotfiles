---
name: review-brief
description: Brief me before I review this session's changes (TLDR, decisions, recap, file-by-file walkthrough, critical pass). Use it whenever you hand finished work over for my review.
argument-hint: "[base ref, commit range or PR URL]"
---

I'm about to review this session's changes myself, and I may not remember what we did. Brief me in chat. Start with these lines, about the non-test changes, and put nothing before them:

- TLDR: what behaves differently before and after this change, in one or two plain sentences. For a visible change, show it with an example, such as a log line, a UI string or a setting.
- TLDR why: why the change is needed. For a bug fix, the symptom it solves as a user sees it.
- Kind: a pure bug fix, a behavior change, or breaking. When the change behaves differently per mode or setting (such as strict and lenient), say what changes in each.
- Worst case: the worst thing this could regress, and in what scenario.
- Tested: what you ran and on what (tests, a dev server, demo players, screenshots), then what is untested. For each hand test only I can do, say whether it blocks shipping.

Then a "Decide" list with each choice that is mine to make: your pick and one line why. Include choices you made yourself that I might not expect, such as overriding a reviewer or keeping something a later change made unnecessary. Leave out what I always do anyway, such as reviewing or approving the push. Leave the list out when there is nothing to decide.

Arguments: `$ARGUMENTS`. Compare against that base ref or PR, or cover only that commit range (`A..B`), otherwise against the merge base with the repo's default branch, taken from upstream when `origin` is my fork. Fetch the base first and name the commit you compare against. Include uncommitted and untracked files. Cover only what this session changed: when the branch also has commits from other work, list them in one line and leave them out of the parts below.

When the diff is under about 20 changed lines, stop after the "Decide" list and one line per changed file.

Write for someone who saw none of the session: no thread ids, finding numbers or names we made up, no bold, and each fact once.

## 1. Recap

Two or three lines:

- Only where it differs from what I asked: changes I didn't ask for, and things I asked for that are missing.
- Scope: what stays the same that I might expect to change, and anything the change needs from another repo or a release.
- PR reviewer comments still unresolved, when the branch has a PR. Find it with `gh pr view` when no PR was given, and read both its comments and its inline review threads (`gh api graphql` on `pullRequest.reviewThreads`, whose `isResolved` says which are open).
- The absolute folder path, the branch and the commit range, on one line.

## 2. File by file

Cover every changed file in one answer, in reading order: entry points and data shapes first, then the code that uses them, tests last. Within a file, go through the changes from top to bottom, in the order they appear in the code, so I can read along. Read the current code rather than relying on what you remember from the session. For each file:

- `path`, then a one-line TLDR, then what changed and why, in a short paragraph.
- Each new name, field, event or case in plain words: what it is, when it happens and what triggers it.
- Why this approach over the obvious alternative, when the choice isn't clear from the code.
- For removals, what was kept and why.
- For tests, which behavior each new test checks.

## 3. Critical pass

When the session already reviewed the diff and fixed what it found (as `implement` step 4 does), start with what was fixed, each with its label, and what was kept on purpose, with the reason. Count kept theoretical findings in one line instead of listing them. Read the diff again as a skeptical reviewer, not its author, for anything that review missed. List only real, specific findings, each labeled as a user-visible bug or reachable but rare. Leave out theoretical ones. Look for:

- edge cases the change adds or misses, such as empty or missing input, ordering, concurrency, and old peers or old data
- tests that only retest existing behavior or would pass without the change
- changes that break callers in this repo or in others

Sort the findings into two lists, each finding with the reason in a few words:

- Worth fixing: what to change and why it matters.
- Not worth fixing: why it can stay as it is.

Don't fix anything. Say whether the branch should ship as one PR or be split, and which commits go where. Close with your recommendation, like "I'd fix 1 and 3. Say go, or tell me what to change.", or "Nothing is worth fixing." when that's the case. When a PR draft follows in the same reply, ask me to say which to fix or to say push, instead of "go".
