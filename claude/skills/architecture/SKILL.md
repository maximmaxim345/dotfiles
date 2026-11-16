---
name: architecture
description: Draw how a change fits together as a diagram, with new, changed and removed parts marked, when it adds a component, moves a responsibility or adds a flow between components
argument-hint: "[PR URL or number, commit range, plan, or empty for the current branch]"
disable-model-invocation: true
---

Target: `$ARGUMENTS`. A PR, a commit range, or empty for the current branch against its merge base with the default branch, uncommitted changes included. `plan` draws the plan in this thread before its code exists: skip step 1, take the planned parts from the plan and the rest from the code it touches, and give each planned part the file it is planned in.

1. Work out the target, fetch its base and note the commit you compare against. For a PR, check out its head as `/review-changes` step 3 says.
2. Decide whether the structure changed: a new component (module, class, service, provider, endpoint, process), a responsibility that moved from one component to another, a new or changed call, message, event or data flow between components, or state stored in a new place. When none did, say so in one line, name the component the change stays inside, and stop.
3. Read the touched components in full, not only the hunks, and follow each one hop out: what calls it and what it calls. Every box and arrow you draw must come from a line you read.
4. Draw one diagram of the structure after the change, with what it was before marked on it:
   - Boxes are components, labeled with their name and file name. Group what the change doesn't touch into one box per area, and keep to about 10 boxes.
   - Arrows show who calls or sends to whom, labeled with the call, message or event name.
   - Mark new boxes and arrows with `--success`, changed ones with `--warning`, and removed ones dashed in `--destructive`. Add a small legend.
   - In T3, check it with `html_preview`, then show it with `html_render`, using the theme variables `html_render` lists. Elsewhere, draw it as text in a code block, with `[new]`, `[changed]` and `[removed]` tags instead of colors.
5. Below the diagram, list each new, changed or removed box or arrow in one line: its absolute `path:line` in backticks, at the base commit for removed ones, and what it does.
6. Below that, add:
   - Alternative: the closest structure you didn't pick, as a second small diagram, and what each of the two costs in one concrete case, like the files that adding one more provider would touch.
   - Locks in: the choices that get expensive to change once other code builds on them.
   - Differs from: how the nearest existing feature solves the same problem, with its absolute `path:line`, and where this one departs from it.
   - For new or changed data shapes, a table of their fields with the type, what writes it and what reads it. Flag a field nothing reads and a type that repeats an existing one.
7. End with a "Decide" list of the structural calls that are mine to make, each with your pick and one line why: a new dependency direction, a component that now knows about another, state stored in a new place, a flow that skips an existing layer. Leave the list out when there are none.
8. Switch `./` back to the branch it was on, or remove the worktree you made.
