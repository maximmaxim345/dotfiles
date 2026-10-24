# OpenCode Config Module (`opencode_config`)

Add a dotfiles module that makes the existing Claude Code prompt files and
commands usable in OpenCode.

## Context

The `claude_config` module installs global instructions, guidelines, commands,
and skills into `~/.claude/`. Those skills already work in OpenCode, because
OpenCode reads the same `~/.claude/skills/*/SKILL.md` path. The commands do not
work in OpenCode, because OpenCode does not expand `@path` references inside a
stored command template. This module bridges that gap.

## Findings (verified, OpenCode v2.1.4)

- OpenCode reads global commands from `~/.config/opencode/commands/`. Project
  commands go in `.opencode/commands/`.
- Stored command templates do not expand `@path`. It stays as ordinary prompt
  text. Attachments come from the composer at invocation time. Source: OpenCode V2
  commands docs (`https://opencode.ai/v2/docs/commands`, "Attachments").
- `$ARGUMENTS`, positional `$1`..`$N`, and `!`shell`` output all expand
  natively in command templates.
- Frontmatter fields are `description`, `agent`, `model`, `subagent`. Unknown
  fields like Claude's `argument-hint` are ignored. `subtask` is a deprecated
  alias for `subagent`.
- Skills already load in OpenCode from `~/.claude/skills/`. No module needed.
- The `implement`, `review-brief`, `blast-radius`, `ma-dev` skills use
  `$ARGUMENTS` in the body. OpenCode loads the body as-is, so `$ARGUMENTS` can
  render literally. Cosmetic only. The skills still function.

## Decisions

- Install path: global, `~/.config/opencode/commands/`.
- Reference handling: inline the referenced prompt files at install time. This
  is required, not optional, because `@path` never expands in a stored template.
- `review-changes` subagent behavior: keep the manual subagent instructions
  (do not convert to OpenCode's native `subagent: true` field).

## Scope

In scope: a new module `opencode_config` that installs four commands with their
prompt references inlined.

Out of scope: the two subagent command variants, which are dropped. Skills need
no module. Prompt guideline files (CLAUDE.md, commit-guidelines.md, etc.) stay
in `~/.claude/` via `claude_config`. This module only consumes them.

Commands in: `commit`, `commit-split`, `open-pr`, `review-changes`.
Commands out (dropped): `commit-subagent`, `commit-split-subagent`.

## Commands and their references

| Command         | `@path` references inlined                                   |
| --------------- | ------------------------------------------------------------ |
| `commit`        | `claude/commit-guidelines.md`                                |
| `commit-split`  | `claude/commit-guidelines.md`                                |
| `open-pr`       | `claude/pr-guidelines.md`, `claude/commit-guidelines.md`, `claude/writing-examples.md` |
| `review-changes`| `claude/writing-examples.md` (plus prose reference to CLAUDE.md) |

The shared commit guidelines also mention `commit-subagent-prompt.md`. Omit
that paragraph and the commands' suggestions to use the excluded variants
from the OpenCode export. Keep the Claude sources unchanged.

## Module design

Extend the existing `df/modules/opencode_config.py`, keeping its global
instructions, OHF Sage agent, dependencies, and backup keys.

Read each command directly from `claude/skills/<name>/SKILL.md` on every render.
Do not maintain a separate set of OpenCode templates or inline markers.

Replace each `@~/.claude/<file>.md` or `~/.claude/<file>.md` reference with the file name and include
that file's current contents in a labeled block after the command body.
Discover references inside included files too, including each file once.
Read these sources from `df.DOTFILES_PATH / "claude"`, not the live home directory.

Preserve command descriptions, arguments, shell blocks, and the manual reviewer
workflow. Export the skill description as command frontmatter and omit skill-only metadata and the excluded subagent prose.
Write the result to `~/.config/opencode/commands/<name>.md`.

Functions: `install`, `uninstall`, `has_update`, `update`.

### Update mechanism (hash)

Store a sha256 of the fully rendered command in the module config, keyed by
command name. The rendered command includes the transformed source command and
all of its included dependencies. `has_update()` returns true when the target
is missing, its contents differ, or the stored hash differs from the freshly
rendered content. `update()` iterates over all defined commands and
rewrites the ones whose hash changed. `install()` writes every command and records
each hash. `uninstall()` restores any backed-up user file and removes the rendered
command.

The hash covers the rendered output, so it factors in every dependency of what is
inlined. Any of these changes the hash and fires an update:

- a referenced prompt file's content changes (a changed link into `claude/`),
- a source command changes or gains, drops, or retargets a reference,
- an included file gains or changes its own references,
- a new command is added to the module (its target file is missing until the first
  `update()` runs over the full defined set).

`update()` iterates the defined commands, not just the configured ones, so newly
added commands are picked up even though they have no stored hash yet.

Back up pre-existing files with `create_backup` on first installation. Keep
that original backup across updates. Replace unmodified generated output without
backing it up. Save locally edited output in a separate backup before replacing
it or uninstalling. Uninstall restores the original files and leaves edit backups
available. Repeated installation and uninstallation are safe.

## Implementation steps

1. Extend `df/modules/opencode_config.py` with the four supported command names.
2. Implement source rendering, recursive dependency inclusion, install, uninstall,
   `has_update`, `update`, and hash storage.
3. Use the existing automatic module discovery.
4. Test rendering, source and dependency updates, missing targets, backup
   preservation, repeated operations, and uninstall in an isolated directory.

## Verification

- `python ./dotfiles.py install opencode_config` writes the four commands to
  `~/.config/opencode/commands/` with prompt content inlined.
- No literal `@~/.claude/` references remain in any rendered command.
- `$ARGUMENTS` and any `!`shell`` blocks are preserved verbatim.
- Editing a source prompt file (e.g. `commit-guidelines.md`) makes
  `has_update()` return true and `update()` rewrite the affected commands.
- `python ./dotfiles.py uninstall opencode_config` restores backed-up files and
  removes the rendered commands.

## Open questions

- Command templates stay in `claude/skills/<name>/SKILL.md`. There is no duplicate OpenCode copy.
- Should `review-changes` later switch to OpenCode's native `subagent: true`
  field instead of manual subagent prose? Deferred. Current plan is manual.
