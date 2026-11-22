---
name: review-brief
description: Brief me before I review this branch's changes (TLDR, decisions, recap, commit-by-commit walkthrough, critical pass). Use it whenever you hand finished work over for my review.
argument-hint: "[base ref, commit range or PR URL] [full]"
---

I'm about to review this branch's changes myself, and I may not remember what we did. Brief me in chat. Start with these lines, about the non-test changes, and put nothing before them:

- TLDR: a table of what behaves differently, one row per behavior, with the columns "Before" and "After". For a visible change, show it in the cell with an example, such as a log line, a UI string or a setting. When only one behavior changes, write one or two plain sentences instead.
- TLDR why: why the change is needed. For a bug fix, the numbered steps a user takes to hit the bug, then one line each for before and after.
- Kind: a pure bug fix, a behavior change, or breaking, compared with the base branch at default settings. When the change behaves differently per mode, setting or side (strict and lenient, legacy clients on and off, server and client), add one line for each that says what changes there.
- Worst case: the worst thing this could regress, and in what scenario.
- Tested: what you ran and with what, each client, device or tool by its name (`sendspin-cpp-cli`, a Python script, the demo players, screenshots), and whether each test fails without the change, then what is untested. Run what you can run yourself before the brief instead of listing it as untested. For each hand test only I can do, say whether it blocks shipping.

Then a numbered "Decide" list with each choice that is mine to make: your pick, one line why, the alternatives as A, B, C with the best reason for each, what could go wrong with your pick, and the evidence (a test, a `path:line`, a measurement, or "none"). I answer "go" to accept every pick, or a number and a letter ("2B") to change one. Order the items riskiest first. For a branch that becomes a PR, how it ships comes before them as the first item: one PR or a split with the commits of each, a bug fix or breaking for each PR, draft or ready, and what it needs from another repo or a release. Include the designs we discussed and dropped, each with why it lost, and choices you made yourself that I might not expect, such as overriding a reviewer or keeping something a later change made unnecessary, and each workaround (such as UI text that steers users around a limitation, or a new hook with a single user) with whether it would pass maintainer review. Leave out what I always do anyway, such as reviewing or approving the push. Leave the list out when there is nothing to decide.

A PR draft in the same reply, as `implement` step 5 asks for, follows the Decide list directly, before the recap.

Arguments: `$ARGUMENTS`. Compare against that base ref or PR, or cover only that commit range (`A..B`), otherwise against the merge base with the repo's default branch, taken from upstream when `origin` is my fork. Fetch the base first and name the commit you compare against. Include uncommitted and untracked files. Cover the whole branch, including commits from earlier sessions or other work, unless I ask for less. `full` shows every hunk in section 2.

When I already reviewed the branch, cover only the commits since that review, unless I ask for more: for each, the commit it fixes, the comment it answers and its hunks as `diff` blocks. Leave out everything else, except what a fix changed in the top lines, and the line with the folder, branch and range. A second brief in the same thread works the same way: say in its first line that it covers only what changed since the last one.

When the diff is under about 20 changed lines, follow the "Decide" list with one line per changed file and its hunks as `diff` blocks, the folder, branch and commit range, and the critical pass findings, and leave out the rest.

Write every code reference, also inside a commit's own entry and for tests, as an absolute `path:line` in backticks. When the branch has a PR, follow each changed-line reference with a link to that line in the PR's diff view, `<PR URL>/files#diff-<sha256 of the repo-relative path>R<line>` (`L<line>` for a removed line), since the file path opens the whole file instead of the diff. Write for someone who saw none of the session: no thread ids, finding numbers or names we made up, no bold, and each fact once.

## 1. Recap

A few short lines:

- Only where it differs from what I asked: changes I didn't ask for, and things I asked for that are missing.
- Scope: what stays the same that I might expect to change, and anything the change needs from another repo or a release.
- PR reviewer comments still unresolved, when the branch has a PR. Find it with `gh pr view` when no PR was given, and read both its comments and its inline review threads (`gh api graphql` on `pullRequest.reviewThreads`, whose `isResolved` says which are open).
- The absolute folder path, the branch, the commit range and the base commit you compared against, on one line.

## 2. Commit by commit

Go through the commits oldest first, with uncommitted changes as one more entry at the end. Write the entries to a file, the path `git rev-parse --path-format=absolute --git-path review-walkthrough.md` prints, replaced on each brief. In chat, show only what this section asks for as `diff` blocks, each under its commit's short hash and subject, then the file's path. Keep the chat brief under about 600 words outside `diff` blocks. With `full`, the whole section goes to chat. Show each `fixup!` commit inside the entry of the commit it fixes, right after it. Read the current code rather than relying on what you remember from the session. For each commit:

- its short hash and subject, then its kind: refactor, behavior, tests or docs. A commit that mixes a refactor with a behavior change counts as behavior, and say which part is which.
- For a refactor, what moved from where to where, and the lines that changed apart from the move. Take those from `~/.claude/skills/review-brief/unmatched_lines.py <commit>`, which prints the lines git doesn't count as part of a moved block: removed lines (`-`) with their place before the commit, added lines (`+`), and under `~` each place where one moved block follows another, which is where lines changed order. Show those and nothing else of the commit.
- For a behavior commit, one line per file: its absolute path and what changed in it. I read the diff in my own viewer, so show a hunk only when it changes a contract (models, commands, events, stored data, migrations, settings, text users see) or a reviewer disagreed with it, or touches what the project rules file lists under "Always look closely", as a fenced `diff` block copied unchanged from `git show`, with its absolute `path:line` and one line on why it needs me. When a hunk runs past about 40 lines, trim its unchanged context lines first.
- For docs, and for text that instructs agents like a skill or a rules file, the changed text as `diff` blocks. In a long line, replace the unchanged parts with `[...]`.
- Each new name, field, event or case in plain words: what it is, when it happens and what triggers it. Add why this approach over the obvious alternative when the code doesn't show it.
- For removals, what was kept and why.
- For tests, which behavior each new test checks.

## 3. Critical pass

When the session already reviewed the diff and fixed what it found (as `implement` step 4 does), start with one line per reviewer (the review subagent, ohf-sage, a reviewer from another model): what it found, what was fixed, each with its label, and what was kept on purpose, with the reason. Count kept theoretical findings in one line instead of listing them. Then say what none of them covered, such as a hand test, and never write that nothing is left to find. When no such review ran, read the diff as a skeptical reviewer, not its author. List only real, specific findings, each labeled as a user-visible bug or reachable but rare. Leave out theoretical ones. Look for:

- edge cases the change adds or misses, such as empty or missing input, ordering, concurrency, and old peers or old data
- tests that only retest existing behavior or would pass without the change
- changes that break callers in this repo or in others

Sort the findings into two lists, each finding with the reason in a few words:

- Worth fixing: what to change and why it matters.
- Not worth fixing: why it can stay as it is.

Don't fix anything. Close with one Ask that names your picks and the next step in full, like "Ask: fix 1 and 3, take the Decide picks as listed, then push as a draft and babysit?", so that accepting the picks is my go-ahead for that step. Write "I found nothing worth fixing." when that's the case.
