---
name: open-pr
description: Commit, push, and open a PR for the current branch, as a prefilled web form, a draft, a draft I babysit, or ready for review, picked in a popup
argument-hint: "[web|draft|ready|babysit]"
---

Read `~/.claude/pr-guidelines.md`, `~/.claude/commit-guidelines.md` and `~/.claude/writing-examples.md` first. Follow the PR guidelines for the PR and the commit guidelines for any commit, and write the description in the voice of the writing examples.

Mode: `$ARGUMENTS`. Empty means I pick it in step 6.

Running this command is not a go-ahead to push. Nothing leaves this machine until I approve it in step 6.

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
   - the PR title
   - the PR description as formatted text, as the writing examples say
   - the target repo and base branch
   - the current branch name, and the proposed one if step 5 proposed one
   - the open PR, when the branch already has one (`gh pr list --repo <target> --head <branch> --state open`)
   Then ask with a popup (AskUserQuestion), or in chat without one:
   - How to open it: Open form (`web`), Ready for review (`ready`), Draft (`draft`), or Draft + babysit (`babysit`). Leave out this question when `$ARGUMENTS` named a mode. When the branch already has an open PR, offer Push only, Push and mark ready, and Push and babysit instead.
   - Whether to request a Copilot review once the PR exists.
   Picking options is the go-ahead for them. A free-text answer asks for changes: revise, post again and ask again. "Open" from me always gets the popup again, never a PR without it. When this session already posted all of this, my latest message is a go-ahead to it, and the branch has no new commits or uncommitted changes since, skip steps 2 to 6.
7. Build the final body: start from the template (if found), fill in the sections using the approved title/description, leave HTML comments intact, and tick any checklist boxes that apply. Write it to a temp file and pass it with `--body-file`. Fold the `fixup!` commits that aren't pushed into the commits they fix, with `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <start>`. `<start>` is `origin/<branch>` after `git fetch origin <branch>` when `git ls-remote --heads origin <branch>` lists the branch, and `$(git merge-base <base> HEAD)` otherwise. When the rebase stops on a conflict, run `git rebase --abort` and ask me. Give a fixup whose target is already pushed a proper message instead. If I approved a new branch name, run `git switch -c <name>` on the default branch or `git branch -m <name>` otherwise, and use the new name as `<branch>` from here on. Push with `git push -u origin HEAD`, then:
   - `web`: needs a working `gh` and a local browser, so not when `CLAUDE_CODE_REMOTE` is `true`. Note the time with `date -u +%Y-%m-%dT%H:%M:%SZ`, then run `gh pr create -w`. The PR not existing afterward is expected, since `-w` only opens the prefilled form. Don't retry without `-w` and don't publish it yourself. Tell me the form is open, that I can pick draft in it, and that this thread picks the PR up on its own once I submit it. Then watch for it as step 8 says.
   - `draft`: run `gh pr create --draft` and give me the PR URL.
   - `ready`: run `gh pr create` and give me the PR URL.
   - `babysit`: run `gh pr create --draft`, give me the PR URL, then follow `~/.claude/skills/babysit/SKILL.md` for it.
   - With an open PR: push only, then run `gh pr ready <n>` for Push and mark ready, or follow the babysit skill for Push and babysit.
   - Request a Copilot review after any of these when I picked it, as `~/.claude/pr-followup.md` says.
   - `web` with a working `gh` but no browser: push only, say why the web form isn't available, and post the title and description again. Create it with `gh pr create --draft` only after a new go-ahead.
   - `draft`, `ready` or `babysit` without a working `gh`: create the PR, as a draft for `draft`, with the GitHub MCP tools when they're available. Then read the PR back, and if the description gained a "Generated by Claude Code" footer, update it to the final body. The go-ahead from step 6 covers this update.
   - `web` without a working `gh`, or the other modes without `gh` or MCP tools: push only and give me the compare URL: `https://github.com/<target>/compare/<base>...<owner>:<branch>?expand=1`.
8. After the web form opens, watch for the PR, since you can't tell when I submit the form. Poll every 30 seconds for up to 30 minutes, in the background with Bash `run_in_background` or the Monitor tool (`timeout_ms` 1800000). `<target>` is the repo the PR targets (the parent for a fork), `<owner>` the owner of the repo you pushed to, and `<time>` the time from step 7. `gh pr list --head` takes only the bare branch name, so the owner filter keeps out PRs from other forks, and the time filter keeps out older PRs from the same branch.
   ```bash
   perl -e 'alarm 1800; exec @ARGV' sh -c 'until gh pr list --repo "$1" --head "$2" --state all --json url,createdAt,headRepositoryOwner --jq ".[] | select(.headRepositoryOwner.login == \"$3\" and .createdAt >= \"$4\") | .url" | grep .; do sleep 30; done' _ <target> <branch> <owner> <time>
   ```
   It prints the PR URL and exits once the PR exists. Then request a Copilot review when I picked it, as `~/.claude/pr-followup.md` says, and link and watch it with your app's PR tools, if it has any, as `~/.claude/pr-followup.md` says. If it ends after 30 minutes without a URL, say so in one line and leave it to me.
