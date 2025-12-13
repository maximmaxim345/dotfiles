# gw - Git Worktree Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a bash CLI tool `gw` for managing git worktrees, installed via dotfiles module.

**Architecture:** Single bash script with subcommands (new, ls, rm, setup). Dotfiles module symlinks script to ~/.local/bin. Script handles worktree detection, branch management, and per-repo setup scripts.

**Tech Stack:** Bash, git, dotfiles module system (Python)

---

### Task 1: Create gw.sh with basic structure and help

**Files:**
- Create: `gw.sh`

**Step 1: Create the script with basic structure**

Create `gw.sh` in dotfiles root:

```bash
#!/bin/bash
set -euo pipefail

# gw - Git Worktree Management Tool

VERSION="1.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_info() {
    echo -e "${BLUE}$1${NC}"
}

show_help() {
    cat << 'EOF'
gw - Git Worktree Management Tool

Usage: gw <command> [options]

Commands:
  new       Create a new worktree
  ls, list  List all worktrees with status
  rm, remove Remove a worktree
  setup     Edit the worktree setup script for this repo

Options:
  -h, --help     Show this help message
  -v, --version  Show version

Examples:
  gw new                    # Interactive: move current branch to worktree
  gw new -b feature-x       # Create new branch 'feature-x' for worktree
  gw new -s refactor        # Put worktree in 'refactor' subfolder
  gw ls                     # List all worktrees
  gw rm                     # Remove current worktree (if in one)
  gw setup                  # Edit .worktree-setup.sh
EOF
}

# Get the main repo directory (works from worktree or main)
get_main_repo() {
    local git_common_dir
    git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)
    if [[ "$git_common_dir" == ".git" ]]; then
        # We're in the main repo
        pwd
    else
        # We're in a worktree, get the main repo path
        dirname "$git_common_dir"
    fi
}

# Check if we're in a git repo
require_git_repo() {
    if ! git rev-parse --git-dir &>/dev/null; then
        print_error "Not in a git repository"
        exit 1
    fi
}

# Main command dispatcher
main() {
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi

    case "$1" in
        new)
            shift
            cmd_new "$@"
            ;;
        ls|list)
            shift
            cmd_list "$@"
            ;;
        rm|remove)
            shift
            cmd_remove "$@"
            ;;
        setup)
            shift
            cmd_setup "$@"
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            echo "gw version $VERSION"
            exit 0
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Placeholder commands - will be implemented in subsequent tasks
cmd_new() {
    print_error "Not implemented yet"
    exit 1
}

cmd_list() {
    print_error "Not implemented yet"
    exit 1
}

cmd_remove() {
    print_error "Not implemented yet"
    exit 1
}

cmd_setup() {
    print_error "Not implemented yet"
    exit 1
}

main "$@"
```

**Step 2: Make script executable**

Run: `chmod +x gw.sh`

**Step 3: Test basic functionality**

Run: `./gw.sh --help`
Expected: Shows help text

Run: `./gw.sh --version`
Expected: Shows "gw version 1.0.0"

Run: `./gw.sh unknown`
Expected: Error message and help text

**Step 4: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): add basic script structure with help"
```

---

### Task 2: Implement gw ls command

**Files:**
- Modify: `gw.sh` (replace cmd_list function)

**Step 1: Replace cmd_list function**

Replace the `cmd_list` placeholder in `gw.sh` with:

```bash
cmd_list() {
    require_git_repo

    local main_repo
    main_repo=$(get_main_repo)

    # Get list of worktrees
    while IFS= read -r line; do
        if [[ -z "$line" ]]; then
            continue
        fi

        # Parse worktree line: path, HEAD, branch
        local wt_path wt_head wt_branch
        wt_path=$(echo "$line" | awk '{print $1}')
        wt_head=$(echo "$line" | awk '{print $2}')
        wt_branch=$(echo "$line" | awk '{print $3}' | sed 's/\[//;s/\]//')

        # Check if this is the main worktree
        local is_main=""
        if [[ "$wt_path" == "$main_repo" ]]; then
            is_main=" [main]"
        fi

        # Get status info for this worktree
        local status_parts=()

        # Count uncommitted changes
        local uncommitted
        uncommitted=$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        if [[ "$uncommitted" -gt 0 ]]; then
            status_parts+=("${uncommitted} uncommitted")
        fi

        # Check ahead/behind status
        local upstream
        upstream=$(git -C "$wt_path" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
        if [[ -n "$upstream" ]]; then
            local ahead behind
            ahead=$(git -C "$wt_path" rev-list --count '@{upstream}..HEAD' 2>/dev/null || echo "0")
            behind=$(git -C "$wt_path" rev-list --count 'HEAD..@{upstream}' 2>/dev/null || echo "0")
            if [[ "$ahead" -gt 0 ]]; then
                status_parts+=("${ahead} ahead")
            fi
            if [[ "$behind" -gt 0 ]]; then
                status_parts+=("${behind} behind")
            fi
        fi

        # Build status string
        local status_str=""
        if [[ ${#status_parts[@]} -eq 0 ]]; then
            status_str="[clean]"
        else
            status_str="[$(IFS=', '; echo "${status_parts[*]}")]"
        fi

        # Print the line
        echo -e "${wt_path} ${BLUE}(${wt_branch})${NC}${is_main} ${status_str}"

    done < <(git -C "$main_repo" worktree list --porcelain | grep -E '^worktree|^HEAD|^branch' | paste - - - | sed 's/worktree //;s/HEAD //;s/branch refs\/heads\///')
}
```

**Step 2: Test the ls command**

Run: `./gw.sh ls`
Expected: Shows current worktree with branch and status

**Step 3: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): implement ls command with status info"
```

---

### Task 3: Implement gw setup command

**Files:**
- Modify: `gw.sh` (replace cmd_setup function)

**Step 1: Replace cmd_setup function**

Replace the `cmd_setup` placeholder in `gw.sh` with:

```bash
cmd_setup() {
    require_git_repo

    local main_repo
    main_repo=$(get_main_repo)

    local setup_script="$main_repo/.worktree-setup.sh"
    local git_exclude="$main_repo/.git/info/exclude"

    # Create template if doesn't exist
    if [[ ! -f "$setup_script" ]]; then
        cat > "$setup_script" << 'TEMPLATE'
#!/bin/bash
# This script runs after creating a new worktree
# Working directory is the new worktree root

# Examples:
# npm install
# pip install -e .
# cp ../.env .env

TEMPLATE
        print_info "Created new setup script: $setup_script"
    fi

    # Ensure it's in .git/info/exclude
    if ! grep -qF '.worktree-setup.sh' "$git_exclude" 2>/dev/null; then
        echo '.worktree-setup.sh' >> "$git_exclude"
        print_info "Added .worktree-setup.sh to .git/info/exclude"
    fi

    # Make executable
    chmod +x "$setup_script"

    # Open in editor
    local editor="${EDITOR:-${VISUAL:-vim}}"
    if ! command -v "$editor" &>/dev/null; then
        editor="nano"
    fi
    if ! command -v "$editor" &>/dev/null; then
        editor="vi"
    fi

    print_info "Opening $setup_script in $editor..."
    "$editor" "$setup_script"

    # Ensure it's still executable after editing
    chmod +x "$setup_script"
    print_success "Setup script saved"
}
```

**Step 2: Test the setup command**

Run: `cd /tmp && git init test-repo && cd test-repo`
Run: `~/dotfiles/gw.sh setup`
Expected: Opens editor with template, creates .worktree-setup.sh, adds to exclude

Run: `cat .git/info/exclude | grep worktree`
Expected: Shows ".worktree-setup.sh"

Run: `ls -la .worktree-setup.sh`
Expected: Shows file is executable

**Step 3: Clean up test repo**

Run: `cd ~ && rm -rf /tmp/test-repo`

**Step 4: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): implement setup command for worktree scripts"
```

---

### Task 4: Implement gw new command

**Files:**
- Modify: `gw.sh` (replace cmd_new function)

**Step 1: Replace cmd_new function**

Replace the `cmd_new` placeholder in `gw.sh` with:

```bash
cmd_new() {
    require_git_repo

    local branch=""
    local subfolder=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -b|--branch)
                branch="$2"
                shift 2
                ;;
            -s|--subfolder)
                subfolder="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: gw new [-b <branch>] [-s <subfolder>]"
                echo ""
                echo "Options:"
                echo "  -b, --branch    Branch name to create (based on current branch)"
                echo "  -s, --subfolder Subfolder to place worktree in"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    local main_repo current_branch upstream_branch repo_name
    main_repo=$(get_main_repo)
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    repo_name=$(basename "$main_repo")

    # Get upstream tracking branch
    upstream_branch=$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null | sed 's|.*/||' || true)
    if [[ -z "$upstream_branch" ]]; then
        # Fallback: try to detect default branch
        upstream_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*/||' || true)
        if [[ -z "$upstream_branch" ]]; then
            # Last resort: common defaults
            for default in main master develop; do
                if git show-ref --verify --quiet "refs/heads/$default"; then
                    upstream_branch="$default"
                    break
                fi
            done
        fi
    fi

    # Interactive prompts if not provided via flags
    if [[ -z "$branch" ]]; then
        echo -n "Branch name (empty to move '$current_branch' to worktree): "
        read -r branch
    fi

    if [[ -z "$subfolder" ]]; then
        echo -n "Subfolder (empty for sibling directory): "
        read -r subfolder
    fi

    # Determine the worktree branch and path
    local wt_branch wt_path

    if [[ -z "$branch" ]]; then
        # Move current branch to worktree
        wt_branch="$current_branch"

        # Check if we're on the upstream branch
        if [[ "$current_branch" == "$upstream_branch" ]]; then
            print_error "Cannot move '$current_branch' to worktree - it's the upstream tracking branch"
            print_info "Specify a branch name with -b to create a new branch"
            exit 1
        fi

        # Check if upstream branch exists
        if [[ -z "$upstream_branch" ]]; then
            print_error "Cannot determine upstream branch to switch to"
            print_info "Specify a branch name with -b to create a new branch instead"
            exit 1
        fi
    else
        # Create new branch based on current
        wt_branch="$branch"
    fi

    # Determine worktree path
    local parent_dir
    parent_dir=$(dirname "$main_repo")

    if [[ -n "$subfolder" ]]; then
        # Put in subfolder: parent/subfolder/reponame
        wt_path="$parent_dir/$subfolder/$repo_name"
    else
        # Sibling: parent/reponame.branchname
        # Sanitize branch name for path (replace / with -)
        local safe_branch
        safe_branch=$(echo "$wt_branch" | tr '/' '-')
        wt_path="$parent_dir/$repo_name.$safe_branch"
    fi

    # Check if path already exists
    if [[ -e "$wt_path" ]]; then
        print_error "Path already exists: $wt_path"
        exit 1
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$wt_path")"

    # Create the worktree
    if [[ -z "$branch" ]]; then
        # Moving current branch - need to switch main repo first
        print_info "Switching main repo to '$upstream_branch'..."
        git -C "$main_repo" checkout "$upstream_branch"

        print_info "Creating worktree with branch '$wt_branch'..."
        git -C "$main_repo" worktree add "$wt_path" "$wt_branch"
    else
        # Creating new branch
        print_info "Creating worktree with new branch '$wt_branch' (based on '$current_branch')..."
        git -C "$main_repo" worktree add -b "$wt_branch" "$wt_path" HEAD
    fi

    # Run setup script if exists
    local setup_script="$main_repo/.worktree-setup.sh"
    if [[ -x "$setup_script" ]]; then
        print_info "Running setup script..."
        if ! (cd "$wt_path" && "$setup_script"); then
            print_warning "Setup script failed (exit code $?), but worktree was created"
        fi
    fi

    # Print success message
    echo ""
    print_success "Created worktree at $wt_path"

    # Calculate relative path for cd command
    local rel_path
    rel_path=$(realpath --relative-to="$(pwd)" "$wt_path")
    echo "Run: cd $rel_path"
}
```

**Step 2: Test the new command (create a test repo first)**

Run:
```bash
cd /tmp
git init test-main
cd test-main
echo "test" > file.txt
git add file.txt
git commit -m "initial"
git checkout -b feature-branch
echo "feature" >> file.txt
git commit -am "feature work"
```

Test interactive mode (move current branch):
Run: `~/dotfiles/gw.sh new` (press Enter twice for defaults)
Expected: Error because no upstream branch configured

Test with new branch:
Run: `~/dotfiles/gw.sh new -b my-feature`
Expected: Creates /tmp/test-main.my-feature with new branch

Run: `ls /tmp/ | grep test-main`
Expected: Shows test-main and test-main.my-feature

**Step 3: Clean up**

Run: `rm -rf /tmp/test-main /tmp/test-main.my-feature`

**Step 4: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): implement new command for creating worktrees"
```

---

### Task 5: Implement gw rm command

**Files:**
- Modify: `gw.sh` (replace cmd_remove function)

**Step 1: Replace cmd_remove function**

Replace the `cmd_remove` placeholder in `gw.sh` with:

```bash
cmd_remove() {
    require_git_repo

    local main_repo current_dir
    main_repo=$(get_main_repo)
    current_dir=$(pwd)

    local force=false
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--force)
                force=true
                shift
                ;;
            -h|--help)
                echo "Usage: gw rm [-f|--force]"
                echo ""
                echo "Options:"
                echo "  -f, --force  Skip clean check (still requires confirmation for dirty)"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    local wt_to_remove=""

    # Check if we're in a worktree (not main repo)
    if [[ "$current_dir" != "$main_repo" ]]; then
        # We're in a worktree - remove current
        wt_to_remove="$current_dir"
    else
        # We're in main repo - show picker
        local worktrees=()
        local wt_info=()

        while IFS= read -r line; do
            local wt_path
            wt_path=$(echo "$line" | awk '{print $1}')

            # Skip the main repo
            if [[ "$wt_path" == "$main_repo" ]]; then
                continue
            fi

            worktrees+=("$wt_path")

            # Get branch and status for display
            local wt_branch uncommitted status_str
            wt_branch=$(git -C "$wt_path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
            uncommitted=$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

            if [[ "$uncommitted" -gt 0 ]]; then
                status_str="[${uncommitted} uncommitted]"
            else
                status_str="[clean]"
            fi

            # Calculate relative path
            local rel_path
            rel_path=$(realpath --relative-to="$main_repo" "$wt_path")
            wt_info+=("$rel_path ($wt_branch) $status_str")

        done < <(git -C "$main_repo" worktree list --porcelain | grep '^worktree ' | sed 's/worktree //')

        if [[ ${#worktrees[@]} -eq 0 ]]; then
            print_info "No worktrees to remove"
            exit 0
        fi

        echo "Worktrees:"
        for i in "${!wt_info[@]}"; do
            echo "  $((i+1))) ${wt_info[$i]}"
        done
        echo ""

        echo -n "Remove which worktree? "
        read -r choice

        if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 ]] || [[ "$choice" -gt ${#worktrees[@]} ]]; then
            print_error "Invalid selection"
            exit 1
        fi

        wt_to_remove="${worktrees[$((choice-1))]}"
    fi

    # Check if worktree is clean
    local uncommitted
    uncommitted=$(git -C "$wt_to_remove" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$uncommitted" -gt 0 ]] && [[ "$force" != true ]]; then
        print_warning "Worktree has $uncommitted uncommitted changes!"
        echo ""
        git -C "$wt_to_remove" status --short
        echo ""
        echo -n "Type 'yes' to force delete: "
        read -r confirm
        if [[ "$confirm" != "yes" ]]; then
            print_info "Cancelled"
            exit 0
        fi
    fi

    # Get the branch name before removing
    local wt_branch
    wt_branch=$(git -C "$wt_to_remove" rev-parse --abbrev-ref HEAD 2>/dev/null || true)

    # Remove the worktree
    print_info "Removing worktree at $wt_to_remove..."

    # If we're inside the worktree, we need to cd out first
    if [[ "$current_dir" == "$wt_to_remove"* ]]; then
        cd "$main_repo"
        print_info "Changed to main repo: $main_repo"
    fi

    git -C "$main_repo" worktree remove --force "$wt_to_remove"

    print_success "Removed worktree at $wt_to_remove"

    # Optionally offer to delete the branch
    if [[ -n "$wt_branch" ]] && [[ "$wt_branch" != "HEAD" ]]; then
        echo -n "Delete branch '$wt_branch'? [y/N] "
        read -r delete_branch
        if [[ "$delete_branch" =~ ^[Yy]$ ]]; then
            if git -C "$main_repo" branch -d "$wt_branch" 2>/dev/null; then
                print_success "Deleted branch '$wt_branch'"
            else
                print_warning "Branch '$wt_branch' has unmerged changes"
                echo -n "Force delete? [y/N] "
                read -r force_delete
                if [[ "$force_delete" =~ ^[Yy]$ ]]; then
                    git -C "$main_repo" branch -D "$wt_branch"
                    print_success "Force deleted branch '$wt_branch'"
                fi
            fi
        fi
    fi
}
```

**Step 2: Test the rm command**

Create test setup:
```bash
cd /tmp
git init test-rm
cd test-rm
echo "test" > file.txt
git add file.txt
git commit -m "initial"
git worktree add ../test-rm.feature feature-branch
```

Test listing (from main repo):
Run: `~/dotfiles/gw.sh rm` (then Ctrl+C to cancel)
Expected: Shows numbered list with test-rm.feature

Test removing from worktree:
Run: `cd /tmp/test-rm.feature && ~/dotfiles/gw.sh rm`
Expected: Removes the worktree

Clean up:
Run: `rm -rf /tmp/test-rm`

**Step 3: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): implement rm command with safety checks"
```

---

### Task 6: Create dotfiles module

**Files:**
- Create: `df/modules/gw.py`

**Step 1: Create the module file**

Create `df/modules/gw.py`:

```python
import io
import platform
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "gw"
NAME: str = "gw (Git Worktree Tool)"
DESCRIPTION: str = "CLI tool for managing git worktrees"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

bin_path = Path.home() / ".local" / "bin" / "gw"
script_path = df.DOTFILES_PATH / "gw.sh"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Ensure ~/.local/bin exists
    bin_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing if present
    if bin_path.exists() or bin_path.is_symlink():
        bin_path.unlink()

    # Create symlink
    df.symlink_path(script_path, bin_path)
    print(f"Symlinked {script_path} -> {bin_path}", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if bin_path.exists() or bin_path.is_symlink():
        bin_path.unlink()
        print(f"Removed {bin_path}", file=stdout)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
```

**Step 2: Test the module loads**

Run: `python ./dotfiles.py list | grep -i worktree`
Expected: Shows "gw (Git Worktree Tool)" in the list

**Step 3: Test install via CLI**

Run: `python ./dotfiles.py install gw`
Expected: Installs successfully

Run: `ls -la ~/.local/bin/gw`
Expected: Shows symlink pointing to dotfiles/gw.sh

Run: `gw --version`
Expected: Shows "gw version 1.0.0"

**Step 4: Test uninstall**

Run: `python ./dotfiles.py uninstall gw`
Expected: Removes the symlink

Run: `ls ~/.local/bin/gw`
Expected: File not found

**Step 5: Reinstall for use**

Run: `python ./dotfiles.py install gw`

**Step 6: Commit**

```bash
git add df/modules/gw.py
git commit -m "feat(gw): add dotfiles module for gw tool"
```

---

### Task 7: Final testing and documentation

**Step 1: Run full integration test**

Create a real test scenario:
```bash
cd /tmp
git init integration-test
cd integration-test
echo "# Test" > README.md
git add README.md
git commit -m "initial"
git remote add origin https://example.com/test.git
git checkout -b develop
echo "develop" >> README.md
git commit -am "develop work"
```

Test full workflow:
1. `gw ls` - should show one worktree
2. `gw setup` - create a setup script (add `echo "setup ran"`)
3. `gw new -b feature-x` - should create worktree and run setup
4. `gw ls` - should show two worktrees
5. `cd ../integration-test.feature-x`
6. `gw rm` - should remove current worktree
7. `gw ls` - should show one worktree

Clean up:
```bash
rm -rf /tmp/integration-test*
```

**Step 2: Commit final version**

```bash
git add -A
git commit -m "feat(gw): complete git worktree management tool" --allow-empty
```

---

## Summary

After completing all tasks, you will have:

1. `gw.sh` - Bash script with commands:
   - `gw new [-b branch] [-s subfolder]` - Create worktrees
   - `gw ls` - List worktrees with status
   - `gw rm` - Remove worktrees with safety
   - `gw setup` - Edit per-repo setup scripts

2. `df/modules/gw.py` - Dotfiles module that symlinks the script

Install with: `python ./dotfiles.py install gw`
