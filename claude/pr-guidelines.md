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
2-4 sentences. Problem and fix, nothing more. Split them into two or three short paragraphs, never one dense block.

For a fix, open with the defect itself in one sentence, including how it happens, then give the scope and impact: who is affected and how badly. Describe the defect, not how it was found, and cut any sentence the reader can already infer from the others.

Example:
> Probe request handling only worked on Docker installations.
>
> Removing the early return fixes playback on Home Assistant OS.
>
> Closes #234

### Medium/Large PRs
Start with a summary sentence. Only add `#` sections if there are truly distinct areas of change worth separating. Don't create a section for every sentence.

### Hand tests
When you or I tried the change by hand on a device or client, end the description with one sentence naming what was tested and the result. This sentence is not a test plan section, and with a template it goes after the filled sections.

### Repo templates
If the repo has a PR template, use it. Fill in its sections rather than replacing it with free-form body.

Tick each checklist box that holds:
- "Tested and works locally" when you or I tried the change on a running build, such as a dev server or demo players.
- Lint, test and build boxes when those ran and passed, apart from failures that also happen on the base branch.
- The AI policy box and a contributor license box, always.
- Boxes about a companion or docs PR only when that PR exists and is linked.

## Links

- When the PR template has a field for related issues, fill it the way the template shows, with only the kind of link the field asks for, never a loosely related PR or page. Leave it empty otherwise. Without such a field, use `Closes #123` when fixing an issue
- `Requires #PR` when blocked on another PR
- Leave a link out rather than guessing its number

## Don't

- Use bold text
- Use dashes as punctuation in prose (em dash, en dash, or a spaced hyphen)
- Over-explain what's obvious from the diff
- Pad with unnecessary words
- Add test plan sections unless explicitly requested

## Creating PRs

Create PRs only through `/open-pr`, which shows the title and body for approval first.
