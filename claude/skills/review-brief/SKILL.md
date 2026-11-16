---
name: review-brief
description: Brief me before I review this branch's changes (TLDR, decisions, recap, commit-by-commit walkthrough, critical pass). Use it whenever you hand finished work over for my review.
argument-hint: "[base ref, commit range or PR URL] [full]"
---

I'm about to review this branch's changes myself, and I may not remember what we did. Brief me in chat. Start with these lines, about the non-test changes, and put nothing before them:

- TLDR: what behaves differently before and after this change, in one or two plain sentences. For a visible change, show it with an example, such as a log line, a UI string or a setting.
- TLDR why: why the change is needed. For a bug fix, the numbered steps a user takes to hit the bug, then one line each for before and after.
- Kind: a pure bug fix, a behavior change, or breaking. When the change behaves differently per mode or setting (such as strict and lenient), say what changes in each.
- Worst case: the worst thing this could regress, and in what scenario.
- Tested: what you ran and on what (tests, a dev server, demo players, screenshots), then what is untested. For each hand test only I can do, say whether it blocks shipping.

Then a "Decide" list with each choice that is mine to make: your pick and one line why. Include choices you made yourself that I might not expect, such as overriding a reviewer or keeping something a later change made unnecessary, and each workaround (such as UI text that steers users around a limitation, or a new hook with a single user) with whether it would pass maintainer review. Leave out what I always do anyway, such as reviewing or approving the push. Leave the list out when there is nothing to decide.

Arguments: `$ARGUMENTS`. Compare against that base ref or PR, or cover only that commit range (`A..B`), otherwise against the merge base with the repo's default branch, taken from upstream when `origin` is my fork. Fetch the base first and name the commit you compare against. Include uncommitted and untracked files. Cover the whole branch, including commits from earlier sessions or other work, unless I ask for less. `full` shows every hunk in section 2.

When I already reviewed the branch, cover only the commits since that review, unless I ask for more: for each, the commit it fixes, the comment it answers and its hunks as `diff` blocks. Leave out everything else, except what a fix changed in the top lines, and the line with the folder, branch and range.

When the diff is under about 20 changed lines, follow the "Decide" list with one line per changed file and its hunks as `diff` blocks, the folder, branch and commit range, and the critical pass findings, and leave out the rest.

Write every code reference, also inside a commit's own entry and for tests, as an absolute `path:line` in backticks. When the branch has a PR, follow each changed-line reference with a link to that line in the PR's diff view, `<PR URL>/files#diff-<sha256 of the repo-relative path>R<line>` (`L<line>` for a removed line), since the file path opens the whole file instead of the diff. Write for someone who saw none of the session: no thread ids, finding numbers or names we made up, no bold, and each fact once.

## 1. Recap

A few short lines:

- Only where it differs from what I asked: changes I didn't ask for, and things I asked for that are missing.
- Scope: what stays the same that I might expect to change, and anything the change needs from another repo or a release.
- PR reviewer comments still unresolved, when the branch has a PR. Find it with `gh pr view` when no PR was given, and read both its comments and its inline review threads (`gh api graphql` on `pullRequest.reviewThreads`, whose `isResolved` says which are open).
- The absolute folder path, the branch, the commit range and the base commit you compared against, on one line.

## 2. Commit by commit

Go through the commits oldest first, in one answer, with uncommitted changes as one more entry at the end. Show each `fixup!` commit inside the entry of the commit it fixes, right after it. Read the current code rather than relying on what you remember from the session. For each commit:

- its short hash and subject, then its kind: refactor, behavior, tests or docs. A commit that mixes a refactor with a behavior change counts as behavior, and say which part is which.
- For a refactor, what moved from where to where, and the lines that changed apart from the move. Take those from `~/.claude/skills/review-brief/unmatched_lines.py <commit>`, which prints the lines git doesn't count as part of a moved block: removed lines (`-`) with their place before the commit, added lines (`+`), and under `~` each place where one moved block follows another, which is where lines changed order. Show those and nothing else of the commit.
- For a behavior commit, the hunks that need my eyes, each as a fenced `diff` block copied unchanged from `git show`, with its absolute `path:line` and one line on why it needs me. These are changes to a contract (models, commands, events, stored data, migrations, settings, text users see), a choice between approaches, ordering or concurrency, and anything a reviewer disagreed with. When a hunk runs past about 40 lines, trim its unchanged context lines first. Give the rest of the commit one line per file.
- For docs, and for text that instructs agents like a skill or a rules file, the changed text as `diff` blocks. In a long line, replace the unchanged parts with `[...]`.
- For each hunk you show: each new name, field, event or case in plain words (what it is, when it happens and what triggers it), its caller and the user action that reaches it, a one-line definition of each existing field it relies on, and why this approach over the obvious alternative when the code doesn't show it.
- For each behavior you say a commit changes, its proof: the test, device run or recording that shows it, the command you ran, and whether the test fails without the change. Write "none" when nothing proves it and "not checked" for what you didn't run.
- For removals, what was kept and why.
- For tests, which behavior each new test checks.

## 3. Critical pass

When the session already reviewed the diff and fixed what it found (as `implement` step 4 does), start with what was fixed, each with its label, and what was kept on purpose, with the reason. Count kept theoretical findings in one line instead of listing them. When no such review ran, read the diff as a skeptical reviewer, not its author. List only real, specific findings, each labeled as a user-visible bug or reachable but rare. Leave out theoretical ones. Look for:

- edge cases the change adds or misses, such as empty or missing input, ordering, concurrency, and old peers or old data
- tests that only retest existing behavior or would pass without the change
- changes that break callers in this repo or in others

Sort the findings into two lists, each finding with the reason in a few words:

- Worth fixing: what to change and why it matters.
- Not worth fixing: why it can stay as it is.

Don't fix anything. Say whether the branch should ship as one PR or be split, and which commits go where. Close with your recommendation, like "I'd fix 1 and 3. Say go, or tell me what to change.", or "Nothing is worth fixing." when that's the case. When a PR draft follows in the same reply, ask me to say which to fix or to say push, instead of "go".
