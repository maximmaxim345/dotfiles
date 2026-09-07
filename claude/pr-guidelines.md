# PR Message Guidelines

## Title

Write for a changelog. Users should understand what changed.

- Use direct verbs: "Fix...", "Add...", "Make...", "Remove...", "Allow..."
- Describe the user-visible effect
- Keep it short (under 10 words ideal)
- Use backticks for code references (e.g., "Add `ComputationContext` for graph execution")

Good:
- "Fix playback on iOS devices"
- "Add `ComputationContext` for flexible graph execution"
- "Make player formats a list of tuples"

Bad:
- "Add support for X" (just say "Add X")
- Technical jargon users won't understand
- Conventional commits (feat:, fix:)
- Vague ("Update code", "Fix bug")

## Body

Keep it short. 2-4 sentences for small PRs. No filler.

Use backticks for code references (`ClassName`, `method_name`, `--flag`).

### Small PRs
2-4 sentences. Problem and fix, nothing more.

Example:
> Probe request handling only worked on Docker installations.
> Removing the early return fixes playback on Home Assistant OS.
>
> Closes #234

### Medium/Large PRs
Start with a summary sentence. Only add `#` sections if there are truly distinct areas of change worth separating - don't create a section for every sentence.

### Repo templates
If the repo has a PR template, you MUST use it. Fill in its sections rather than replacing it with free-form body.

## Links

- `Closes #123` - when fixing an issue
- `Requires #PR` - when blocked on another PR

## Don't

- Use bold text
- Use dashes (-, em dash, en dash) in prose
- Over-explain what's obvious from the diff
- Pad with unnecessary words
- Add test plan sections unless explicitly requested

## Creating PRs

When asked to create a PR, always use `-w`:
```
gh pr create -w --title "..." --body "..."
```
The `-w` flag opens the PR in the browser for review before publishing. Always
use it, no exceptions.

`-w` does not create the PR. It opens the create form prefilled with your title
and body. The user reviews and publishes from there. So after running it, the
PR will not yet exist in `gh pr view` or `gh pr list` and that is expected and
correct. Do not treat the missing PR as a failure, do not retry without `-w`,
and do not publish it yourself.

If the user asks for a draft PR, still use `-w` (not `--draft`) and tell them to
select the draft option in the browser form.
