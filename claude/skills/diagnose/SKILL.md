---
name: diagnose
description: Find the cause of a bug before fixing it, by reproducing it first and testing one hypothesis at a time. Use when I report something broken, failing, slow or flaky, or ask you to debug or diagnose it, before you change code to fix it.
argument-hint: "[what's broken]"
---

Bug: $ARGUMENTS

1. Reproduce it first. Find the cheapest command that shows the bug the way I described it, such as a failing test, a script or a request against a dev server, and run it. Show the command and the lines of its output that show the bug. For a bug that shows only now and then, run it until it fails often enough to tell a fix from luck. When you can't reproduce it, stop and tell me what you tried and what you need from me, such as logs, a device or access.
2. State one hypothesis: what causes the bug, and the observation that would disprove it. Pick the one the reproduction and the code point to most.
3. Test it with one change at a time, such as a log line, a breakpoint or a changed value, and run the reproduction again after each. Start every debug log line with the same marker, like `[debug]`, so you can find and remove all of them.
4. When the observation disproves the hypothesis, undo its changes and go back to step 2. After two disproved hypotheses, stop and report the reproduction, each hypothesis with what disproved it, and what you would try next.
5. Once a hypothesis holds, remove the debug lines and tell me the cause and the reproduction in a few lines. When I only asked for the cause, stop there. When I asked for a fix, go on with `implement` step 2 in a repo listed under "Project rules" in my CLAUDE.md, and elsewhere fix it with a test that fails before the fix, where a test can reach the bug the way it happens.
