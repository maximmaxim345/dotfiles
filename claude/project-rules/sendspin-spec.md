# Sendspin spec

- `README.md` is generated. Edit the split sources and run `python3 tools/build-readme.py --check`.
- Design stance: simple client, all-knowing server. Keep each role self-contained and limit cross-role links.
- Use the spec's exact terms and conditions. Don't soften a MUST or invent a condition.
- Keep a rule's reason out of the normative text. The reason goes in the PR description.
- Do spec reviews and edits yourself. Use ohf-sage only when I ask.
- In reviews, drop findings that only matter when the other side breaks the spec, and don't treat a "such as" list as a requirement.
- The spec is pre-1.0. Don't hold PRs to compatibility or version-bump rules.
- Flag wording only when it changes the meaning or leaves an ambiguity a real implementer would hit.
