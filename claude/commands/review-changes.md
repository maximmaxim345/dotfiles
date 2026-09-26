---
description: Review a PR or the local changes with parallel reviewers, verify every finding, and draft inline comments in my voice
argument-hint: "[PR number or URL] [sage|nosage]"
---

Write every comment in the voice of @~/.claude/writing-examples.md and follow the "Review comment style" and "Writing style" rules in `CLAUDE.md`.

Arguments: `$ARGUMENTS`. A PR number or URL reviews that PR. Without one, review `./` in local mode (see the end). `sage` forces ohf-sage on, `nosage` turns it off.

Running this command is not a go-ahead to post. Nothing goes to GitHub until I approve it in step 9. When `gh` isn't available, use the GitHub MCP tools for every read and write below.

1. Find the PR. Run `gh pr view <pr> --json number,url,title,body,author,baseRefName,headRefName,headRepositoryOwner,headRefOid,files,additions,deletions,commits` and confirm the repo, since the shell cwd can reset between commands. Read the repo's file in `~/.claude/project-rules/` if it has one.
2. Gather context before reading the diff:
   - the issues and PRs linked in the description, and the discussion on them
   - for Sendspin, the spec at `origin/main`, and for library PRs, the library version the PR targets
   - the PR's CI results and the repo's linter config
   Fetch the base branch and note the commit you compare against. If I already submitted a review, focus on the commits since that review's commit. Don't read existing reviews and comments yet, so they don't steer the review. Step 7 uses them to drop duplicates.
3. Check out the PR head. If `./` is already on it, review there. Otherwise run `gh pr checkout <pr>` in `./`, or without `gh`, `git fetch origin pull/<number>/head:pr-<number>` and check out `pr-<number>`, unless it has uncommitted changes or the current branch has unpushed commits. In that case create a worktree under `<repo>/.claude/worktrees/pr-<number>` and say why. Note the branch `./` was on before.
4. Decide on ohf-sage. Run it for Music Assistant, Sendspin, ESPHome, and OHF-Voice PRs, except Sendspin spec PRs and small PRs. A PR is small when it changes a few lines in one or two files and makes no design choice, like a version bump or a typo fix. `sage` and `nosage` override this.
5. Start the reviewers in the background, in parallel:
   - A fresh general-purpose subagent. Give it the PR URL, the checkout path, the base commit, the project rules file, the linked context, and the sorting rules at the end of step 7. Tell it not to read the PR's existing reviews and comments. It looks for bugs, spec or project-rule violations, and code that doesn't fit its surroundings, reads whole files rather than only the hunks, and may run tests to confirm a suspected bug. It reports each finding as `path:line`, what's wrong, how to trigger it, and the exact spec or code line it depends on. It posts nothing to GitHub.
   - ohf-sage, when step 4 says so, reviewing the same diff against the project standards.
6. For PRs that aren't small, post a walkthrough in chat while the reviewers run: what problem the PR solves, how the change flows through the code, and what looks surprising. I may ask questions about it before the findings come in.
7. Verify the findings. First read the existing reviews, inline comments and their threads (including Copilot's and mine), my pending review's comments from `gh api repos/<owner>/<repo>/pulls/<number>/reviews/<id>/comments`, and the results file from an earlier run (see step 8). Dismiss findings they already raise, settled, or dismissed. Then merge duplicates across reviewers, and treat findings several reviewers agree on as one finding, not as extra confidence. Then send every finding to one fresh subagent with only its `path:line` and a one-line claim, not the reviewer's reasoning, and have it try to disprove each one. Then check what survives yourself: open the source that proves or disproves it, and run a test when that settles it. A user-visible bug stays in To post only when a test, a repro, or a traced call path confirms it. For a spec violation, quote the MUST or SHOULD clause and check the text against each of its conditions. A finding without that proof moves to Lower priority as a "Question:". Then sort each one:
   - Dismissed: the spec or code already covers it elsewhere (search the whole repo before calling something a gap), it depends on a different version than the PR targets, the PR or its linked discussion chose it on purpose, it conflicts with another PR I own, an existing comment already covers it, a linter or CI check already catches it, or it's theoretical.
   - Lower priority: an issue the PR didn't introduce or make worse, a wording or naming nit, or a case that needs a misbehaving peer and does no lasting harm. A misbehaving peer that can crash, hang, or corrupt state is a real finding.
   - To post: everything else, ranked with user-visible bugs first, then reachable but rare ones.
8. Write the results to `<repo>/.claude/reviews/pr-<number>.md`, the results file. `<repo>` is the main checkout, not a worktree, so the file survives worktree removal. Before writing it, add `.claude/reviews/` to `$(git rev-parse --git-common-dir)/info/exclude` if it isn't there yet, and never stage or commit the file. Use three sections, "To post", "Lower priority", and "Dismissed", separated by `---`. Each entry is a `### path:line` heading on the PR's side of the diff, then the comment. Dismissed entries get one line with the reason and stay in the file for later runs. A finding about a line outside the diff goes in the review body instead. When a finding has a small, clear fix, offer a local fix commit on the PR branch instead of a comment. Pushing it needs its own go-ahead. Then post in chat:
   - a tally by type, like "2 bugs, 1 question, 4 nits"
   - the top 2 or 3 findings to post, then the rest
   - the lower priority and dismissed findings, one line each
   - how existing comments cover the rest
   - whether ohf-sage ran and why
   - the base commit and how much of the diff you read
   When I edit or reject a comment, update the file and post the changed entries again.
9. Continue only when my latest message is an explicit go-ahead. Create a pending review with the approved comments, on `headRefOid`, with `side` set to `RIGHT`. Leave out `event`, so the review stays pending and only I can see it:
   `gh api repos/<owner>/<repo>/pulls/<number>/reviews -X POST --input <file>`
   With the GitHub MCP tools, read the comments back afterward. If any gained a "Generated by Claude Code" footer, update them to the approved text, or tell me which ones have it when the tools can't. If I already have a pending review on this PR, stop and tell me instead. Never submit, approve, or request changes. Give me the PR's files URL so I can edit and submit it myself.
10. When I say the review is done, remove the worktree if you made one, or switch `./` back to the branch it was on. Then list the comments I rewrote and ask whether to add any of them to `~/.claude/writing-examples.md`.

## Local mode

Review the changes in `./` against its merge base with the default branch, including uncommitted ones. Nothing goes to GitHub in this mode.
- Instead of steps 1 to 3, fetch the default branch, find the base with `git merge-base HEAD origin/<default>`, and diff `./` against it. Also review the untracked files that `git ls-files --others --exclude-standard` lists. Read the repo's project rules, and for Sendspin, the spec at `origin/main`.
- Run steps 4 to 7 as written, with small meaning a small diff. For the linter check in step 7, run the repo's linters on the changed files in check-only mode. Skip a tool that can only fix files in place.
- The results file is `<repo>/.claude/reviews/local-<branch>.md`, with each `/` in the branch name replaced by `-`. In step 8, describe each finding with a suggested fix instead of a comment for someone else. Don't change any code until I ask.
- Skip steps 9 and 10.
