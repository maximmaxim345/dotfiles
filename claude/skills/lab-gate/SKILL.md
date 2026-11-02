---
name: lab-gate
description: Run a Music Assistant server PR through the end-to-end test lab, only for the areas its diff touches
argument-hint: "[PR number]"
disable-model-invocation: true
---

PR: `$ARGUMENTS`, or the open PR of the current branch when empty. Find it with `gh pr view <pr> --repo music-assistant/server --json number,url,headRefOid,files`, or with no argument `gh pr view --json number,url,headRefOid,files` from the branch's checkout, since `--repo` needs a number. With no argument and no open PR for the branch, stop and ask for a number.

The lab lives in `~/projects/end-to-end-test-lab`. Its CLI is `bin/lab` there, which syncs the checkout to the lab VM and runs `labctl` over `ssh lab`. Below, `lab` means that path.

## Steps

1. Run `ssh lab true`. If it fails, the VM is off: say so in one line and stop. Otherwise `git -C ~/projects/end-to-end-test-lab pull --ff-only`, since `lab` ships that checkout's tests to the VM.
2. When run from the PR's branch, compare `git rev-parse HEAD` with `headRefOid`. The lab fetches the PR from GitHub, so name any local commits that aren't pushed and say they won't be tested.
3. Map every changed file to its areas and `--providers` entries with "Path to area" in `docs/pr-gate.md` of the lab repo. Read it every time, since the map changes. Paths there are relative to `server/music_assistant/`. Take the union of the areas and the union of the provider entries.
4. If no file maps to an area or a provider entry (docs, tests only), the result is `skipped`. A provider that `pr-gate.md` lists as "no lab coverage" also gives `skipped`, with that as the note.
5. A `models/**` change maps to `--all`, the full gate. Run it only when I asked for the full gate. Otherwise the result is `full gate not run`.
6. Run the areas in the background and wait for them. Runs beyond the lab's capacity queue.

       lab run --ref pr/<n> --areas <area>[,<area>]

   Player provider rows (`--providers squeezelite` and so on) are their own command, not part of the `--areas` one: next to `--areas`, `--providers` only picks the players. Put the player domains of all such rows in one:

       lab run --ref pr/<n> --providers <domain>[,<domain>]

   For a device row or a music provider row, use the `--providers` command `pr-gate.md` gives for it. Never run `--deep`.

## Reading the result

- Exit 0 is green. The lab reruns a failing gate (`--areas`, `--all`, player providers) once by itself, so a red gate means a test failed twice. Device and music runs have no rerun.
- The CLI prints the run id. `lab summary <run id>` gives the failures per area. For more, read `/srv/lab/runs/<id>/summary.json` and `junit.xml` over `ssh lab`, and `lab logs <id>` for the server log. Runbook: `docs/runbook.md`, section "Reading a failed run".
- For each red test, check whether it also fails on `dev`: look for a recent `dev` run in `lab runs --ref dev`, or rerun the command that failed with `--ref dev -k <test>`. If it fails on `dev` too, the result is `dev-red`: a lab or `dev` problem, not this PR.

## Output

The areas run, the result (`green`, `red`, `dev-red`, `unreachable`, `skipped` or `full gate not run`), the run ids, and for red the failing tests with a one-line reason each.
