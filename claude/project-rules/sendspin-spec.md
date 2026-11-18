# Sendspin spec

- `README.md` is generated. Edit the split sources and run `python3 tools/build-readme.py --check`.
- Design stance: simple client, all-knowing server. Keep each role self-contained and limit cross-role links.
- Use the spec's exact terms and conditions. Don't soften a MUST or invent a condition.
- Keep a rule's reason out of the normative text. The reason goes in the PR description.
- Do spec reviews and edits yourself. Use ohf-sage only when I ask.
- In reviews and proposals, drop findings and rules that only matter when the other side breaks the spec, and don't treat a "such as" list as a requirement.
- Before proposing a rule, quote the existing rules that touch the case and prefer the smallest change.
- Before showing new normative wording, grep each new term and use the spec's existing one, drop sentences an existing rule already implies, and check that no sentence contradicts its neighbors.
- When a turn changes spec text or asks to push, include the full current PR title and description before the Ask line.
- The spec is pre-1.0. Don't hold PRs to compatibility or version-bump rules. A behavior change still ends its PR description with a "Breaking changes" section that says whether clients, servers or both must update, and which first.
- Flag wording only when it changes the meaning or leaves an ambiguity a real implementer would hit.
- Leave per-connection scope implied. Don't add "on the same connection" to a rule.
- Dynamic pairing code is the primary pairing method, ahead of static code and pairing PSK. Never call a dynamic-flow rule low-impact.
- Clients see no paused state. A paused group is `playback_state: 'stopped'` with metadata and artwork kept, so don't propose pause rules for clients.
