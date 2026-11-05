---
name: second-opinion
description: Have reviewers from other models check the current change, a PR or spec text, picked with their reasoning effort in a popup
argument-hint: "[PR URL or number, commit range, or what to check]"
disable-model-invocation: true
---

Target: `$ARGUMENTS`. A PR reviews that PR, a range reviews those commits, and other words name what to check, like a spec proposal in this thread. Empty means the current branch against its merge base with the default branch, uncommitted changes included.

1. Work out the target, fetch its base and note the commit you compare against. For a PR, check out its head as `/review-changes` step 3 says. For Sendspin work, also note the spec commit at `origin/main`.
2. Ask with popups (AskUserQuestion):
   - First, which reviewers, as a multi-select: GPT-6 Astra through OpenCode (your pick, first), GPT-6.1 Sol through OpenCode, a Claude Opus subagent, and "More reviewers". "More reviewers" asks which provider, from the enabled ones `orchestrator_capabilities` lists in T3 (OpenCode alone elsewhere), then, in one popup, which models from each picked provider.
   - Then the reasoning effort for each picked reviewer, one question per reviewer and up to four per popup: medium (your pick), low, high, and "More efforts", which asks again with the other levels that model offers.
3. Write one brief for all reviewers: the target, the checkout path, the base commit, the project rules file, for Sendspin the spec commit, and what the change is meant to do in one or two sentences. Paste text from this thread, like a spec proposal, in full. Leave out your own findings and conclusions. Each reviewer reads whole files rather than only the hunks, checks the tests first, posts nothing and changes no files, and reports each finding as `path:line`, what's wrong, how to trigger it, and the spec or code line it depends on.
4. Start the picked reviewers in parallel, each at its picked effort. The model ids are `gpt-6-astra` and `gpt-6.1-sol`. In T3, use `delegate_task` in plan mode with the target `{providerInstanceId: 'opencode', model: 'github-copilot/<id>', options: {variant: '<effort>'}}`, or the provider and model I picked, with the effort under the option name `orchestrator_capabilities` gives that model. Elsewhere, run `cd <checkout> && opencode run -m github-copilot/<id>#<effort> --agent plan` in the background. Use the Agent tool with the Opus model and the picked effort for the Claude subagent.
5. Check each finding against the source yourself, merge duplicates, and drop what this thread already found or settled. Label the rest user-visible bug, reachable but rare, or theoretical, and leave out theoretical ones. Reply with which reviewer found what, each finding as an absolute `path:line`, and say which reviewers found nothing.
6. Switch `./` back to the branch it was on, or remove the worktree you made.
