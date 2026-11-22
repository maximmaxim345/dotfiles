---
name: review-brief
description: Brief me before I review this branch's changes (TLDR, decisions, recap, a review page with the diff in reading order, critical pass). Use it whenever you hand finished work over for my review.
argument-hint: "[base ref, commit range or PR URL]"
---

I'm about to review this branch's changes myself, and I may not remember what we did. Brief me in chat, and for a larger change also on a review page built with the review kit (`~/.claude/review-kit/README.md`). Start the chat brief with these lines, about the non-test changes, and put nothing before them except the PR's URL when `implement` step 5 puts it first:

- TLDR: a table of what behaves differently, one row per behavior, with the columns "Before" and "After". For a visible change, show it in the cell with an example, such as a log line, a UI string or a setting. When only one behavior changes, write one or two plain sentences instead.
- TLDR why: why the change is needed. For a bug fix, the numbered steps a user takes to hit the bug, then one line each for before and after.
- Kind: a pure bug fix, a behavior change, or breaking, compared with the base branch at default settings. When the change behaves differently per mode, setting or side (strict and lenient, legacy clients on and off, server and client), add one line for each that says what changes there.
- Worst case: the worst thing this could regress, and in what scenario.
- Tested: what you ran and with what, each client, device or tool by its name (`sendspin-cpp-cli`, a Python script, the demo players, screenshots), and whether each test fails without the change, then what is untested, without repeating the Worst case or the "Decide" list. Run what you can run yourself before the brief instead of listing it as untested. For each hand test only I can do, say whether it blocks shipping.

Then a numbered "Decide" list with each choice that is mine to make: your pick, one line why, the alternatives as A, B, C with the best reason for each, what could go wrong with your pick, and the evidence (a test, a `path:line`, a measurement, or "none"). I answer "go" to accept every pick, or a number and a letter ("2B") to change one. Order the items riskiest first. For a branch that becomes a PR, how it ships comes before them as the first item: one PR or a split with the commits of each, a bug fix or breaking for each PR, draft or ready, and what it needs from another repo or a release. Include the designs we discussed and dropped, each with why it lost, and choices you made yourself that I might not expect, such as overriding a reviewer or keeping something a later change made unnecessary, and each workaround (such as UI text that steers users around a limitation, or a new hook with a single user) with whether it would pass maintainer review. Leave out what I always do anyway, such as reviewing or approving the push. Leave the list out when there is nothing to decide.

A PR draft in the same reply, as `implement` step 5 asks for, follows the Decide list directly.

Arguments: `$ARGUMENTS`. Compare against that base ref or PR, or cover only that commit range (`A..B`), otherwise against the merge base with the repo's default branch, taken from upstream when `origin` is my fork. Fetch the base first and name the commit you compare against. Include uncommitted and untracked files. Cover the whole branch, including commits from earlier sessions or other work, unless I ask for less.

List the hunks with `python3 ~/.claude/review-kit/build_review.py review --repo <checkout> --base <base commit> --head <head sha> --list-hunks --json`, or `--range A..B` in place of both, adding `--uncommitted` when the checkout has uncommitted or untracked files. When its `tier` is `small` and the whole diff, tests included, has under about 50 changed lines, follow the "Decide" list and any PR draft with one line per changed file and its hunks as `diff` blocks, then the recap and the critical pass, and build no page. Otherwise build the page as section 2 says.

When I already reviewed the branch, cover only what changed since that review, unless I ask for more: pass the head I reviewed, from `reviewed-head` in the page folder (section 2), as `--since` to the same commands, and build a round two page whose `feedback` has one item per comment I made, with the hunks that answer it. When its `tier` is `fixup`, or the change since is as small as above, show instead, for each comment, the commit that answers it and its hunks as `diff` blocks, and build no page. Leave out everything else, except what a fix changed in the top lines, and the line with the folder, branch and range. A second brief in the same thread works the same way, with the head of the last brief as `--since`: say in its first line that it covers only what changed since the last one.

My answer is the text of the page's Copy for chat button, or typed the same way: `go` accepts every pick, `2B, 4C` changes those picks, and each further paragraph `<where>: <text>` is a comment on that line or hunk, or on a round two item when `<where>` starts with `Reply to`. When it arrives, write the full sha of the head the brief covered to `reviewed-head` in the page folder, replacing what is there, also when no page was built. When the brief included uncommitted changes, write that head anyway, and the next round shows them again.

Write every code reference, also for tests, as an absolute `path:line` in backticks. When the branch has a PR, follow each changed-line reference with a link to that line in the PR's diff view, `<PR URL>/files#diff-<sha256 of the repo-relative path>R<line>` (`L<line>` for a removed line), since the file path opens the whole file instead of the diff. Write for someone who saw none of the session: no thread ids, finding numbers or names we made up, no bold, and each fact once.

## 1. Recap

A few short lines in chat, also on the page as `facts` labeled "Not asked", "Missing", "Scope", "Open comments" and "Partner", except the folder line:

- Only where it differs from what I asked: changes I didn't ask for, and things I asked for that are missing.
- Scope: what stays the same that I might expect to change, and anything the change needs from another repo or a release.
- PR reviewer comments still unresolved, when the branch has a PR. Find it with `gh pr view` when no PR was given, and read both its comments and its inline review threads (`gh api graphql` on `pullRequest.reviewThreads`, whose `isResolved` says which are open).
- The partner thread, linked, when one runs for a companion PR (`~/desk/TASK.md`, "Companion PRs").
- The absolute folder path, the branch, the commit range and the base commit you compared against, on one line.

## 2. Review page

Write the narrative as the kit's README says, from the current code rather than what you remember of the session. The brief maps onto it: `branch` its name, `title` and `behavior` from the TLDR, `summary` from TLDR why and Kind, `worst_case`, `tested`, `decide` from the "Decide" list in the same order, `facts` from the recap, `claims` with the proof of each behavior from Tested, and `reviewers` from the critical pass. When no review ran, your own pass is one reviewer named "Own pass", with its two findings lists as its `note` and no `fixed`, `kept` or `skipped`. `groups` set the reading order, most important first:

- A hunk that needs me gets a `note` with one line on why: it changes a contract (models, commands, events, stored data, migrations, settings, text users see) or a reviewer disagreed with it. The kit tags the paths its `review-paths.json` lists. Also note each hunk that "Always look closely" in the project rules file covers. Add `context` when I need unchanged code to follow it.
- The note of the hunk that adds a new name, field, event or case says in plain words what it is, when it happens and what triggers it, and why this approach over the obvious alternative when the code doesn't show it. For removals, what was kept and why. For tests, which behavior each new test checks.
- Hunks that don't need me go in groups marked `unimportant`, each with a one-line `reason`. A commit's kind is refactor, behavior, tests or docs, and one that mixes a refactor with a behavior change counts as behavior. For a refactor commit, the reason says what moved from where to where, and each line that changed apart from the move gets a note. A hunk that a later commit also changed stays out of that group, with a note on what changed after the move. Take the changed lines from `~/.claude/skills/review-brief/unmatched_lines.py <commit>`, run in the checkout, which prints the lines git doesn't count as part of a moved block: removed lines (`-`) with their place before the commit, added lines (`+`), and under `~` each place where one moved block follows another, which is where lines changed order.

The page folder is `<git common dir>/review-pages/<branch with each / as ->`, with the common dir from `git rev-parse --path-format=absolute --git-common-dir`, and the checkout folder's name in place of the branch on a detached HEAD, unless I name another folder. Build `review-<short head>.html` from `review-<short head>.json` there with the listing's flags, `--narrative <json> -o <html>`. Fix each reference it rejects, and check that each hunk it reports as not mentioned needs no note. The chat brief keeps everything this skill asks for except the hunks, with the page's absolute path in backticks before the folder line. When the branch changes docs or spec text that becomes a PR, that changed text stays in chat as `diff` blocks. Keep it under about 600 words outside the TLDR table, the "Decide" list and the PR draft. Give the page by its path, not as an inline render.

## 3. Critical pass

When the session already reviewed the diff and fixed what it found (as `implement` step 4 does), start with one line per reviewer (the review subagent, ohf-sage, a reviewer from another model): how many findings it fixed per label, and what was kept on purpose, with the reason. The fixed findings go on the page's reviewers section, or in chat when there is no page. Count kept theoretical findings in one line instead of listing them. Then say what none of them covered, such as a hand test, and never write that nothing is left to find. When no such review ran, read the diff as a skeptical reviewer, not its author. List only real, specific findings, each labeled as a user-visible bug or reachable but rare. Leave out theoretical ones. Look for:

- edge cases the change adds or misses, such as empty or missing input, ordering, concurrency, and old peers or old data
- tests that only retest existing behavior or would pass without the change
- changes that break callers in this repo or in others

Sort the findings into two lists, each finding with the reason in a few words:

- Worth fixing: what to change and why it matters.
- Not worth fixing: why it can stay as it is.

Don't fix anything. Close with one Ask that names your picks and the next step in full, like "Ask: fix 1 and 3, take the Decide picks as listed, then push as a draft and babysit?", so that accepting the picks is my go-ahead for that step. Write "I found nothing worth fixing." when that's the case.
