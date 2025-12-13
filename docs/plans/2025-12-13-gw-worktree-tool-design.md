# gw - Git Worktree Management Tool

## Overview

A bash script `gw` for managing git worktrees, installed via dotfiles module.

**Commands:**
- `gw new` - create a new worktree
- `gw ls` / `gw list` - show worktrees with status
- `gw rm` / `gw remove` - remove worktrees
- `gw setup` - edit repo's worktree setup script

## Installation

- Dotfiles module: `df/modules/gw.py`
- Script: `gw.sh` in dotfiles root
- Symlinked to `~/.local/bin/gw`
- Linux/macOS only

## Commands

### `gw new`

Creates a new worktree with smart defaults.

**Interactive prompts (when flags not provided):**
1. "Branch name (empty to move current branch):"
2. "Subfolder (empty for sibling directory):"

**Flags:**
- `-b <branch>` - branch name to create
- `-s <subfolder>` - subfolder to organize into

**Branch behavior:**
- If branch name provided: create new branch based on current branch, use it for worktree
- If empty: move current branch to worktree, switch main repo to upstream tracking branch
- Error if on upstream tracking branch and no branch name given

**Path resolution:**
```
# No subfolder:
~/projects/myrepo  →  ~/projects/myrepo.branchname

# With subfolder "refactor":
~/projects/myrepo  →  ~/projects/refactor/myrepo
```

**After creation:**
1. Run `.worktree-setup.sh` if exists (warn on failure, keep worktree)
2. Print absolute path
3. Print relative `cd` command

**Example output:**
```
Created worktree at /home/user/projects/myrepo.feature-x
Run: cd ../myrepo.feature-x
```

**Worktree detection:** If run from within a worktree, operates as if run from main repo.

### `gw ls` / `gw list`

Shows worktrees with status info:

```
/home/user/projects/myrepo (main) [bare]
/home/user/projects/myrepo.feature-x (feature-x) [3 uncommitted]
/home/user/projects/myrepo.bugfix (bugfix) [clean, 2 ahead]
```

**Status indicators:**
- `[bare]` - main worktree marker
- `[clean]` - no changes
- `[N uncommitted]` - uncommitted changes count
- `[N ahead]` / `[N behind]` - vs upstream tracking branch

### `gw rm` / `gw remove`

**When in a worktree:**
1. Check if working tree is clean (no uncommitted, no untracked)
2. If clean: confirm and remove
3. If dirty: show warning, require typing `yes` to force delete

**When in main repo:**
1. Show numbered list of worktrees (excluding main)
2. User picks a number
3. Same clean/dirty logic

**Example:**
```
$ gw rm
Worktrees:
  1) ../myrepo.feature-x (feature-x) [clean]
  2) ../myrepo.bugfix (bugfix) [2 uncommitted]

Remove which worktree? 2

Warning: worktree has uncommitted changes!
Type 'yes' to force delete: yes
Removed worktree at /home/user/projects/myrepo.bugfix
```

### `gw setup`

Manages the per-repo setup script.

1. Opens `$EDITOR` (fallback: `vim`, `nano`) with `.worktree-setup.sh`
2. Creates template if file doesn't exist:
   ```bash
   #!/bin/bash
   # This script runs after creating a new worktree
   # Working directory is the new worktree root

   ```
3. Adds `.worktree-setup.sh` to `.git/info/exclude`
4. Makes script executable

**Script execution (during `gw new`):**
- Working directory: new worktree root
- Non-zero exit: warning printed, worktree kept

## Files

- `gw.sh` - main script (dotfiles root)
- `df/modules/gw.py` - dotfiles module
- `.worktree-setup.sh` - per-repo setup script (in each repo, git-ignored)
