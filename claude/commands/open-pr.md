Follow @~/.claude/pr-guidelines.md to create a pull request.

1. Run `git diff main...HEAD` (or appropriate base branch) to see all changes
2. Run `git log main...HEAD --oneline` to see commit history
3. Look for a PR template in the repo:
   - Check `.github/PULL_REQUEST_TEMPLATE.md` first
   - Then `.github/pull_request_template.md`
   - Then `PULL_REQUEST_TEMPLATE.md` at the repo root
   - Then `.github/PULL_REQUEST_TEMPLATE/` directory (multiple templates)
   If a template exists, use it as the base for the PR body. Fill in the template sections with content from the diff/commits. Leave HTML comments (`<!-- ... -->`) from the template intact in the body.
4. Draft a PR title and a short description (the meaningful content only: what changed and why). Skip boilerplate sections like checklists, "Types of changes", and template placeholders at this stage.
5. Show the draft title and description to the user and ask for feedback before proceeding. Wait for approval or edits.
6. Once approved, build the final body: start from the template (if found), fill in the sections using the approved title/description, leave HTML comments intact, and tick any checklist boxes that apply.
7. Create the PR with `gh pr create -w --title "..." --body "..."`

The `-w` flag opens the PR in browser for review before publishing.
