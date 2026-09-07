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
| `prompts.md` | Standalone prompts to paste into other agents |
| `commit-guidelines.md` | Referenced by the commit commands |
| `pr-guidelines.md` | Referenced by `open-pr` |
| `commit-subagent-prompt.md` | Prompt for the commit subagent |
| `commands/` | Slash commands, linked as a whole directory so new ones need no module change |
| `output-styles/` | Output styles, linked as a whole directory |

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
mkdir -p "$CLAUDE_DIR"

RAW=https://raw.githubusercontent.com/maximmaxim345/dotfiles/main/claude
STRIP_FRONTMATTER='NR==1 && /^---$/ {f=1; next} f && /^---$/ {f=0; next} !f'

# Cloud runners ignore output-styles/, so the style is appended to the instructions instead.
{
  curl -fsSL "$RAW/CLAUDE.md"
  printf '\n\n# Output style\n\n'
  curl -fsSL "$RAW/output-styles/plain-english.md" | awk "$STRIP_FRONTMATTER"
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

The agent and its 8M corpus download in under a second, so they fit the setup
script's time budget comfortably. The runner needs
`release-assets.githubusercontent.com` reachable for the release assets, on top
of `raw.githubusercontent.com` for the instructions, so both belong in the
environment's allowed domains.

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
