# Claude Code config

The hand-authored part of `~/.claude`. Installed by the `claude_config` module,
which symlinks each entry below into `~/.claude`, so a `git pull` makes changes
live on every device without re-running anything.

```bash
./dotfiles.py install claude_config
```

| File | Purpose |
| --- | --- |
| `CLAUDE.md` | Global instructions, applied to every project |
| `commit-guidelines.md` | Referenced by the commit skills and commands |
| `pr-guidelines.md` | Referenced by `open-pr` |
| `commit-subagent-prompt.md` | Prompt for the commit subagent |
| `writing-examples.md` | Examples of my GitHub writing voice, read by `CLAUDE.md` |
| `commands/` | Claude-only slash commands, linked as a whole directory so new ones need no module change |
| `output-styles/` | Output styles, linked as a whole directory |
| `project-rules/` | Per-repo rules, read on demand as listed in `CLAUDE.md` |
| `skills/` | My workflow skills (`implement`, `commit`, `commit-split`, `open-pr`, `review-changes`), each linked into `~/.claude/skills/` |

Not to be confused with the repository root `CLAUDE.md`, which is a symlink to
`AGENTS.md` and describes this repo as a project. The file here is the global
user config.

## Not covered by the module

`settings.json` is deliberately untracked, because Claude Code rewrites it on
every `/config` change and plugin toggle. So on a new device these are set up by
hand:

- **The output style has to be selected**, with `/output-style Plain English`.
  The style file is symlinked, but the selection lives in `settings.local.json`.
- **Everything else in `settings.json`**: model, `effortLevel` and
  `modelSettings`, `tui`, `voice`, `permissions.defaultMode`, the attribution
  blanking, and the skip-prompt flags.
- **Skills**, which come from `~/.agents/.skill-lock.json`. All of them are
  third-party, so they are installed from their upstreams rather than tracked
  here. Their on/off curation is the `skillOverrides` key in `settings.json`.
- **Plugins and marketplaces**, the `enabledPlugins` and
  `extraKnownMarketplaces` keys in `settings.json`.

The `ohf-sage` agent has its own module, `ohf_sage`, because it is third-party
and publishes weekly releases. It downloads the agent and its corpus from
`github.com/chrisuthe/ohf-sage` and reports an update when a new release lands,
rather than freezing a copy in this repo.

```bash
./dotfiles.py install ohf_sage
```

## Claude Code Web

Cloud sessions do not see any of the above. Per the
[documentation](https://code.claude.com/docs/en/cloud-environments), a runner
gets its own home directory, so nothing under your local `~/.claude` carries
over: not the global `CLAUDE.md`, not user-level commands, agents or hooks, and
nothing in `settings.json` or `settings.local.json`.

What does reach a cloud session:

- Anything committed inside the repo being worked on, which arrives with the
  clone. That covers the repo's own `CLAUDE.md` and its `.claude/` directory,
  including `settings.json`, `commands/`, `agents/`, `skills/` and `.mcp.json`.
- Skills and plugins enabled on your claude.ai account, which sync separately.
- Whatever a setup script installs.

A setup script is the only route for user-level config. Add one under the cloud
icon at `claude.ai/code`, via **Add cloud environment**, in the **Setup script**
field. It runs once before Claude Code launches, must exit zero within about
five minutes, and its result is cached until the script changes or the
environment expires after roughly a week.

```bash
#!/usr/bin/env bash
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DOTFILES="$HOME/.cache/dotfiles"
mkdir -p "$CLAUDE_DIR"

rm -rf "$DOTFILES"
git clone --depth 1 https://github.com/maximmaxim345/dotfiles.git "$DOTFILES"

# Link the same entries as the claude_config module, so the CLAUDE.md imports and commands resolve.
for src in "$DOTFILES"/claude/*; do
  name=$(basename "$src")
  case "$name" in README.md | CLAUDE.md | skills) continue ;; esac
  ln -sfn "$src" "$CLAUDE_DIR/$name"
done

mkdir -p "$CLAUDE_DIR/skills"
for src in "$DOTFILES"/claude/skills/*; do
  ln -sfn "$src" "$CLAUDE_DIR/skills/$(basename "$src")"
done

# The grilling skill that /implement uses, from the same upstream as the local skill lock.
MATT="$HOME/.cache/mattpocock-skills"
rm -rf "$MATT"
git clone --depth 1 https://github.com/mattpocock/skills.git "$MATT"
ln -sfn "$MATT/skills/productivity/grilling" "$CLAUDE_DIR/skills/grilling"

# Cloud runners start without user settings, so attribution is turned off here.
cat >"$CLAUDE_DIR/settings.json" <<'JSON'
{
  "attribution": { "commit": "", "pr": "", "sessionUrl": false }
}
JSON

STRIP_FRONTMATTER='NR==1 && /^---$/ {f=1; next} f && /^---$/ {f=0; next} !f'

# Cloud runners ignore output-styles/, so the style is appended to the instructions instead.
{
  cat "$DOTFILES/claude/CLAUDE.md"
  printf '\n\n# Output style\n\n'
  awk "$STRIP_FRONTMATTER" "$DOTFILES/claude/output-styles/plain-english.md"
} >"$CLAUDE_DIR/CLAUDE.md"

# The OHF Sage agent, the same release assets the ohf_sage module installs locally.
SAGE=https://github.com/chrisuthe/ohf-sage/releases/latest/download
mkdir -p "$CLAUDE_DIR/agents"
curl -fsSL -o "$CLAUDE_DIR/agents/ohf-sage.md" "$SAGE/ohf-sage.md"
curl -fsSL -o "$CLAUDE_DIR/agents/ohf-sage-corpus.jsonl" "$SAGE/ohf-sage-corpus.jsonl"
# The shipped corpus path is project relative and resolves to nothing outside a project root.
sed -i.bak "s|\.claude/agents/ohf-sage-corpus\.jsonl|$CLAUDE_DIR/agents/ohf-sage-corpus.jsonl|g" \
  "$CLAUDE_DIR/agents/ohf-sage.md"
rm -f "$CLAUDE_DIR/agents/ohf-sage.md.bak"

# Install uv through its own installer, which avoids the GitHub API rate limit.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The platform rewrites `~/.gitconfig` with `Claude <noreply@anthropic.com>`
after the setup script runs, so the git identity can't be set from the script.
It's set as environment variables of the cloud environment instead, which
override `.gitconfig` for both author and committer:

```
GIT_AUTHOR_NAME=Maxim Raznatovski
GIT_AUTHOR_EMAIL=nda.mr43@gmail.com
GIT_COMMITTER_NAME=Maxim Raznatovski
GIT_COMMITTER_EMAIL=nda.mr43@gmail.com
```

The platform's stop hook, `~/.claude/stop-hook-git-check.sh`, still flags these
commits as unverifiable and tells the agent to re-author them as Claude. It is
provisioned again for every session, so it can't be patched from here.
`CLAUDE.md` tells agents to ignore it instead.

The agent and its 8M corpus download in under a second, so they fit the setup
script's time budget comfortably. The runner needs
`release-assets.githubusercontent.com` reachable for the release assets, on top
of `github.com` for the dotfiles clone, so both belong in the environment's
allowed domains.

This is confirmed working on a cloud runner. User-level agents do not sync to a
web session on their own, but a runner does discover them from
`~/.claude/agents/`, because the setup script writes them there before Claude
Code launches. A test session with `HOME=/root` listed `ohf-sage`, resolved the
rewritten corpus path, and answered with citations from the corpus.

Two things worth knowing about that script. The `awk` drops the style's YAML
frontmatter, which would otherwise land mid-file as stray `---` lines. And the
style's own closing "Precedence" section says that `CLAUDE.md` overrides it,
which reads oddly once the style is part of `CLAUDE.md`, but it changes nothing
in practice and keeping the concatenation mechanical avoids maintaining a
second copy of the style.

## Codex and Copilot

Two more modules build the same setup for Codex and GitHub Copilot. Both depend
on `claude_config`, since the skills read files like
`~/.claude/commit-guidelines.md` by path, and on `agent_skills`, which links
every skill in `skills/` into `~/.agents/skills/`, where both tools look.

```bash
./dotfiles.py install codex_config copilot_config
```

`codex_config` writes `~/.codex/AGENTS.md`, which is `CLAUDE.md` with the
writing examples inlined and the output style appended, because Codex reads a
single instructions file and has no imports. It also turns the OHF Sage agent into
`~/.codex/agents/ohf-sage.toml` when `ohf_sage` is installed. The generated
files are rewritten by `./dotfiles.py update` whenever their sources change.
`skills/implement/agents/openai.yaml` keeps Codex from starting `implement` on
its own, since Codex ignores `disable-model-invocation`.

Codex stops reading instruction files once they add up to 32 KiB, counting the
global file and the repo's own `AGENTS.md` together. The global file alone is
about 24 KiB, so raise the limit by hand in `~/.codex/config.toml`, which the
module leaves alone:

```toml
project_doc_max_bytes = 131072
```

`copilot_config` writes the same combined instructions to
`~/.copilot/instructions/global.instructions.md`, a folder both Copilot CLI and
the Copilot app read, with `applyTo: "**"` since files there only apply to the
paths they match. Two agents go into `~/.copilot/agents/`:

- `implement`, because Copilot CLI can't reach a skill with
  `disable-model-invocation` at all
  ([copilot-cli#4438](https://github.com/github/copilot-cli/issues/4438)).
  Start it with `/agent implement`.
- `ohf-sage`, a short agent that reads the full `~/.claude/agents/ohf-sage.md`,
  because Copilot caps an agent's instructions at 30,000 characters.

Neither tool is tested here yet. Things to check on first use: that the Copilot
app lists the instructions file under "File-backed instructions", that
`/agent implement` works, and that `codex "Summarize the current instructions."`
shows these rules.

### Codex cloud (experimental, untested)

Like Claude Code on the web, Codex cloud tasks start without any user-level
config. The environment's setup script is the only way in, so this installs the
modules there. Whether the cloud agent reads `~/.codex/AGENTS.md` and
`~/.agents/skills/` written this way is undocumented.

```bash
#!/usr/bin/env bash
set -euo pipefail

DOTFILES="$HOME/.cache/dotfiles"
rm -rf "$DOTFILES"
git clone --depth 1 https://github.com/maximmaxim345/dotfiles.git "$DOTFILES"
cd "$DOTFILES"
python3 dotfiles.py install ohf_sage
python3 dotfiles.py install codex_config
echo "project_doc_max_bytes = 131072" >>"$HOME/.codex/config.toml"
```

The container is cached for up to 12 hours, and "Reset cache" on the environment
page forces a fresh run. The same `GIT_AUTHOR_*` and `GIT_COMMITTER_*` variables
as above go into the environment's variables, though which identity Codex cloud
commits with is also undocumented.
