---
name: open-pr
description: Commit, push, and open a PR for the current branch, as a draft, a draft I babysit, ready for review, or babysat through to the merge, picked in a popup. Use when I say open, ship or push for a branch, never without my go-ahead.
argument-hint: "[draft|ready|babysit|merge]"
---

Read `~/.claude/pr-guidelines.md`, `~/.claude/commit-guidelines.md` and `~/.claude/writing-examples.md` first. Follow the PR guidelines for the PR and the commit guidelines for any commit, and write the description in the voice of the writing examples.

Mode: `$ARGUMENTS`. Empty means I pick it in step 6.

Running this command is not a go-ahead to push. Nothing leaves this machine until I approve it in step 6, or a desk item's start note allows it as `implement` step 5 says.

1. Find the target repo. Run `gh repo view --json nameWithOwner,parent,defaultBranchRef` and confirm it reports the repo this branch belongs to, since the shell cwd can reset between commands. If it has a `parent`, this is a fork: the PR targets the parent, so pass `--repo <parent> --head <owner>:<branch>` later. If `gh` is missing or `gh auth status` fails, note it and continue, step 7 falls back.
2. Commit any uncommitted changes following the commit guidelines. Then check every commit in `git log <base>..HEAD` for Claude, Codex, or Copilot attribution (`Co-Authored-By` trailers, "Generated with" lines). If there is any, stop and tell me.
3. Run `git diff <base>...HEAD` and `git log <base>..HEAD --oneline` to see the whole change.
4. Look for a PR template in the repo:
   - Check `.github/PULL_REQUEST_TEMPLATE.md` first
   - Then `.github/pull_request_template.md`
   - Then `PULL_REQUEST_TEMPLATE.md` at the repo root
   - Then `.github/PULL_REQUEST_TEMPLATE/` directory (multiple templates)
   If a template exists, use it as the base for the PR body. Fill in the template sections with content from the diff/commits. Leave HTML comments (`<!-- ... -->`) from the template intact in the body.
5. Draft a PR title and a short description (the meaningful content only: what changed and why). Skip boilerplate sections like checklists, "Types of changes", and template placeholders at this stage.
   Then check the branch name, unless `CLAUDE_CODE_REMOTE` is `true` (keep the branch the session assigned):
   - On the default branch: propose a new `<type>/<slug>` branch with a Conventional Commits type.
   - On a branch without an upstream that `git ls-remote --heads origin <branch>` doesn't list, with an auto-generated name or one that no longer matches the change: propose a `<type>/<slug>` name.
   - Never rename a branch that exists on the remote, since the old one would stay on GitHub.
6. Post in chat, then ask as below and wait for the answer:
   - the subject and body of each commit on the branch, as they will be after step 7 folds the `fixup!` commits
   - the PR title, and two alternative titles
   - the screenshots you'd add, only when the change makes a visible difference
   - the PR description as formatted text, as the writing examples say
   - the target repo and base branch
   - the current branch name, and the proposed one if step 5 proposed one
   - the open PR, when the branch already has one (`gh pr list --repo <target> --head <branch> --state open`)
   Then ask with a popup (AskUserQuestion), or in chat without one:
   - How to open it: Draft + babysit (`babysit`, your pick, first), Draft (`draft`), Ready for review (`ready`), or, for a fix under about 50 changed lines in a repo where I merge my own PRs, Babysit, then ready and merge (`merge`). Leave out this question when `$ARGUMENTS` named a mode. When the branch already has an open PR, offer Push only, Push and mark ready, and Push and babysit instead.
   - Which automatic review to request once the PR exists: none, Copilot, or, when the target repo is in the `music-assistant` org, Bot-MArley.
   Picking options is the go-ahead for them. A free-text answer asks for changes: revise, post again and ask again. "Open" from me always gets the popup again, never a PR without it. When I accepted an Ask of yours that named the mode and showed this draft, that answer replaces the popup, also after the fixes that Ask named. When this session already posted all of this, in chat or on the review page, my latest message is a go-ahead to it, and the branch has no new commits or uncommitted changes since, skip steps 2 to 6.
7. Build the final body: start from the template (if found), fill in the sections using the approved title/description, leave HTML comments intact, and tick any checklist boxes that apply. Reference each approved screenshot in the body as `![<alt>](<path>)` and pass it with `--attach '<path>#<alt>'` to `gh pr create`, or to `gh pr edit <number>` for an open PR. Write the body to a temp file and pass it with `--body-file`. Note the tip with `git rev-parse HEAD`, then fold the `fixup!` commits that aren't pushed into the commits they fix, with `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <start>`. `<start>` is `origin/<branch>` after `git fetch origin <branch>` when `git ls-remote --heads origin <branch>` lists the branch, and `$(git merge-base <base> HEAD)` otherwise. When the rebase stops on a conflict, run `git rebase --abort` and ask me. After the fold, stop and tell me when `git diff --quiet <noted tip> HEAD` finds a difference. Give a fixup whose target is already pushed a proper message instead. If I approved a new branch name, run `git switch -c <name>` on the default branch or `git branch -m <name>` otherwise, and use the new name as `<branch>` from here on. Push with `git push -u origin HEAD`, then:
   - `draft`: run `gh pr create --draft` and give me the PR URL.
   - `ready`: run `gh pr create` and give me the PR URL.
   - `babysit`: run `gh pr create --draft`, give me the PR URL, then follow `~/.claude/skills/babysit/SKILL.md` for it.
   - `merge`: as `babysit`. When it stops clean (checks pass, a review bot reviewed the last commit, no thread is open, no person commented), mark the PR ready and merge it as `~/.claude/pr-followup.md` says. Otherwise stop and ask as babysit does.
   - With an open PR: push only, then run `gh pr ready <n>` for Push and mark ready, or follow the babysit skill for Push and babysit.
   - Request the review I picked after any of these, then link and watch the PR, as `~/.claude/pr-followup.md` says.
   - `draft`, `ready` or `babysit` without a working `gh`: create the PR, as a draft for `draft`, with the GitHub MCP tools when they're available. Then read the PR back, and if the description gained a "Generated by Claude Code" footer, update it to the final body. The go-ahead from step 6 covers this update.
   - Without `gh` or MCP tools: push only and give me the compare URL: `https://github.com/<target>/compare/<base>...<owner>:<branch>?expand=1`.

## Stacked PRs

GitHub's native stacked PRs work through the `gh stack` extension (`github/gh-stack`), and music-assistant/server has them enabled. For a stack:
- Open each layer through this skill, bottom up, with `--base` set to the branch below it (the default branch for the bottom one). One approval in step 6 can cover all layers when the drafts for each were shown.
- Then link them with `gh stack link <bottom PR> ... <top PR>`, which prints the stack number. Grow a stack later with `gh stack link <stack number> <new branch or PR>`.
- Don't use `gh stack submit`: its editor can't run in an agent session, and `--auto` replaces our titles and bodies with generated ones.
- Carry fixups up the stack with `gh stack rebase`, and ask before each push as usual. Don't run `gh stack merge` unless I ask.
