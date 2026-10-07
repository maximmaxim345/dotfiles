---
name: review-brief
description: Brief me before I review this session's changes (recap, what's left, file-by-file walkthrough, critical pass).
argument-hint: "[base ref or PR URL]"
disable-model-invocation: true
---

I'm about to review this session's changes myself, and I may not remember what we did. Brief me in chat, in the four parts below. Start with a one or two sentence TLDR of what the change does.

Arguments: `$ARGUMENTS`. Compare against that base ref or PR, otherwise against the merge base with the repo's default branch, taken from upstream when `origin` is my fork. Fetch the base first and name the commit you compare against. Include uncommitted and untracked files. Cover only what this session changed: when the branch also has commits from other work, list them in one line and leave them out of the parts below.

## 1. Recap

- What I asked for and what was built, one or two sentences each, from the whole session rather than the last turn.
- Changes I didn't ask for, and things I asked for that are missing.
- The absolute folder path, the branch and the commit range.

## 2. Before I read

- Questions still waiting on me, and work left for later or for another PR.
- Review findings that were skipped or kept on purpose, one line each.
- What is untested: changed code that no test run in this session exercised, and behavior stated without a test run or file read that proves it.
- Whether every reviewer comment on the branch's PR is addressed. Find the PR with `gh pr view` when no PR was given, and read both its comments and its inline review threads (`gh api graphql` on `pullRequest.reviewThreads`, whose `isResolved` says which are open). List the unresolved ones.

Say "none" for a part with nothing in it.

## 3. File by file

Cover every changed file in one answer, in reading order: entry points and data shapes first, then the code that uses them, tests last. Read the current code rather than relying on what you remember from the session. For each file:

- `path`, then what changed and why, in a short paragraph.
- Each new name, field, event or case in plain words: what it is, when it happens and what triggers it.
- For tests, which behavior each new test checks.

## 4. Critical pass

Read the diff again as a skeptical reviewer, not its author. List only real, specific findings, each labeled as a user-visible bug or reachable but rare. Leave out theoretical ones. Look for:

- edge cases the change adds or misses, such as empty or missing input, ordering, concurrency, and old peers or old data
- tests that only retest existing behavior or would pass without the change
- changes that break callers in this repo or in others

Don't fix anything. End with a one or two sentence TLDR of why the change is needed. Then ask which findings I want fixed.
