## Review and ship

What I can say in any thread, and what it does.

- "ship": push, mark the PR ready, post the approved replies and resolve their threads, ask each bot that reviewed before to review again (Bot-MArley with `@Bot-MArley recheck`), or Copilot when none did, and keep watching the PR.
- "continue", in answer to a question about pushing: push.
- "local commits", in answer to a review of someone else's PR: fix the findings as commits on their PR branch instead of drafting a pending review.
- "finish", after local commits: push to the contributor's branch, approve their CI run when it comes from a fork, resolve the fixed threads, post the replies, file backlog items for points left for later, approve in my voice, squash merge, and switch back.
- `/review-changes <PR>`, or "start a review" in the board's Incoming chat: review someone else's PR, and ask how to test it before I approve it.
- `/review-brief`: brief me on the whole branch before I review it.
- `/architecture [PR or range]`: a diagram of how the change fits together, when its structure changed.
- `/second-opinion [PR or range]`: popups pick reviewers from other models and the effort for each, then it says which reviewer found what.
- `/blast-radius`: what a change could break outside its diff.
- `/open-pr`: commit, push and open the PR, with a popup for the mode and the bot review (none, Copilot, or Bot-MArley in `music-assistant` repos).
- `/babysit <PR>`: watch the PR until CI is green and the review bots have nothing open.
- `/lab-gate <PR>`: run a Music Assistant server PR through the test lab.

## A review of someone else's PR

1. Start it with `/review-changes <PR>`.
2. While the reviewers run, read a normal or large PR in T3's PR Guide tab (PR Guides on in T3's settings).
3. A short card arrives with the PR, its size, the comments to post, and a choice between local commits and a pending review.
4. Answer "local commits", pick a test in the popup, then say "finish". Or pick the pending review and post it yourself on GitHub.

## Without asking

- Agents fold their own unpushed fixups.
- Each stage of a long run ends with a "Left:" line.
- A question about pushing or posting shows the full draft.
- Drafts I post myself, like Discord messages, get no question.
- File paths come in backticks so they're clickable, with full GitHub URLs at the end of the reply.
- Review briefs cover the whole branch and list who calls each changed function.

## Board

Incoming entries have "tomorrow" and "next week" snooze links, which also end when the entry gets news other than a board move. Hide asks first and lasts until the entry gets news other than a board move. The desk's chat answers stay for a day, with an "item" link to what the desk filed.
