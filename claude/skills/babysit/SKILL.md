---
name: babysit
description: Watch my PR until CI is green and the review bots have nothing open, pushing fixes and replying to bots on its own within a fixed scope
argument-hint: "[PR URL or number]"
disable-model-invocation: true
---

PR: `$ARGUMENTS`, or the open PR of the current branch when empty. Confirm it with `gh pr view <pr> --json number,url,isDraft,headRefName,headRepositoryOwner`, since the shell cwd can reset between commands.

Typing this command, or picking babysit in `/open-pr`, is my OK for these actions on this PR until you stop, without asking each time:
- Push commits to its head branch that fix failing CI or a review bot finding you verified. Never force push.
- Reply to review bot threads, and resolve the ones you fixed or dismissed with a reason.
- After each push, request a new review from each review bot that reviewed before, the way it expects: `gh pr edit <n> --repo <owner/repo> --add-reviewer @copilot` for Copilot, a comment for a bot that takes commands (like `@Bot-MArley recheck`).

A review bot is Copilot or any account GitHub marks as a bot. When the repo's project rules or the bot's earlier comments show it needs a request to start, request it once at the start.

Everything else still needs my OK, asked with a popup (AskUserQuestion): replies to people (draft them as `~/.claude/pr-followup.md` says), a force push, a rebase or merge of the base branch, marking the PR ready, editing its title or description, merging, and any finding you're unsure about or whose fix goes beyond it.

## Loop

1. Watch the PR as `~/.claude/pr-followup.md` says.
2. On a failed check, reproduce it locally, fix it and commit.
3. On review bot findings, verify each against the code, since bots are often wrong or miss context. Fix the valid ones as commits. For the rest, reply in my voice (see `~/.claude/writing-examples.md`) with the reason in one or two sentences.
4. Push once per round, then reply to and resolve the threads you handled, and request the bots' reviews again.

Stop when the checks on the latest commit pass, a review bot reviewed that commit, and no bot thread is open. Then report in a few lines what you pushed, replied to and resolved. When the PR is a draft, ask with a popup whether to mark it ready for review.

Also stop and ask when a person reviews or comments, when I write in this thread, or when the same check fails after two fixes.
