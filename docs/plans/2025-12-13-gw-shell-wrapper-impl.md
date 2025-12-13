# gw Shell Wrapper Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `gw cd` command and shell wrapper for auto-cd after worktree operations.

**Architecture:** Add `cmd_cd` function to gw.sh with interactive picker. Add shell wrapper function to zshrc and bashrc that parses "Run: cd ..." output and executes the cd.

**Tech Stack:** Bash, zsh

---

### Task 1: Add `gw cd` command to help text

**Files:**
- Modify: `gw.sh:39-60` (show_help function)

**Step 1: Update help text**

Find the show_help function and add `cd` to the Commands section:

```bash
Commands:
  new       Create a new worktree
  ls, list  List all worktrees with status
  rm, remove Remove a worktree
  cd        Switch to another worktree
  setup     Edit the worktree setup script for this repo
```

**Step 2: Test help shows new command**

Run: `./gw.sh --help`
Expected: Shows `cd` in Commands list

**Step 3: Commit**

```bash
git add gw.sh
git commit -m "docs(gw): add cd command to help text"
```

---

### Task 2: Add `cd` to command dispatcher

**Files:**
- Modify: `gw.sh:93-120` (main function case statement)

**Step 1: Add cd case to dispatcher**

Add after the `setup)` case (around line 108):

```bash
        cd)
            shift
            cmd_cd "$@"
            ;;
```

**Step 2: Add placeholder cmd_cd function**

Add after cmd_setup function (before `main "$@"`):

```bash
cmd_cd() {
    print_error "Not implemented yet"
    exit 1
}
```

**Step 3: Test dispatcher recognizes cd**

Run: `./gw.sh cd`
Expected: "Error: Not implemented yet"

**Step 4: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): add cd command placeholder"
```

---

### Task 3: Implement `cmd_cd` function

**Files:**
- Modify: `gw.sh` (replace cmd_cd placeholder)

**Step 1: Implement cmd_cd with interactive picker**

Replace the placeholder `cmd_cd` function with:

```bash
cmd_cd() {
    require_git_repo

    local main_repo
    main_repo=$(get_main_repo)

    # Build list of all worktrees
    local worktrees=()
    local wt_info=()

    while IFS= read -r wt_path; do
        [[ -z "$wt_path" ]] && continue

        worktrees+=("$wt_path")

        # Get branch and status for display
        local wt_branch uncommitted status_str is_main=""
        wt_branch=$(git -C "$wt_path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        uncommitted=$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

        if [[ "$wt_path" == "$main_repo" ]]; then
            is_main=" [main]"
        fi

        if [[ "$uncommitted" -gt 0 ]]; then
            status_str="[${uncommitted} uncommitted]"
        else
            status_str="[clean]"
        fi

        # Calculate relative path
        local rel_path
        rel_path=$(get_relative_path "$wt_path" "$(pwd)")
        wt_info+=("$rel_path ($wt_branch)$is_main $status_str")

    done < <(git -C "$main_repo" worktree list --porcelain | grep '^worktree ' | sed 's/worktree //')

    if [[ ${#worktrees[@]} -eq 0 ]]; then
        print_info "No worktrees found"
        exit 0
    fi

    if [[ ${#worktrees[@]} -eq 1 ]]; then
        print_info "Only one worktree exists (current)"
        exit 0
    fi

    echo "Worktrees:"
    for i in "${!wt_info[@]}"; do
        echo "  $((i+1))) ${wt_info[$i]}"
    done
    echo ""

    echo -n "Switch to which worktree? "
    read -r choice

    if [[ -z "$choice" ]]; then
        print_info "Cancelled"
        exit 0
    fi

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 ]] || [[ "$choice" -gt ${#worktrees[@]} ]]; then
        print_error "Invalid selection"
        exit 1
    fi

    local selected_path="${worktrees[$((choice-1))]}"
    local rel_path
    rel_path=$(get_relative_path "$selected_path" "$(pwd)")

    echo "Run: cd $rel_path"
}
```

**Step 2: Test cd command**

Run: `./gw.sh cd` (in a repo with worktrees)
Expected: Shows numbered list, after selection prints "Run: cd <path>"

**Step 3: Commit**

```bash
git add gw.sh
git commit -m "feat(gw): implement cd command with interactive picker"
```

---

### Task 4: Add shell wrapper to zshrc

**Files:**
- Modify: `zsh/zshrc` (after dz function, around line 60)

**Step 1: Add gw wrapper function**

Add after the `dz()` function (around line 60):

```bash
# gw wrapper - auto-cd after new/rm/cd
if command -v gw &>/dev/null; then
    gw() {
        local output pwd_before
        pwd_before="$PWD"
        output=$(command gw "$@")
        echo "$output"

        # Check last line for "Run: cd ..."
        local last_line cd_path
        last_line=$(echo "$output" | tail -1)
        if [[ "$last_line" == "Run: cd "* ]]; then
            cd_path="${last_line#Run: cd }"
            cd "$cd_path" && echo "→ Changed to $(pwd)"
        # For gw rm: if current directory no longer exists, go to main repo
        elif [[ ! -d "$pwd_before" ]]; then
            local main_repo
            main_repo=$(echo "$output" | grep "Changed to main repo:" | sed 's/.*Changed to main repo: //')
            if [[ -n "$main_repo" && -d "$main_repo" ]]; then
                cd "$main_repo" && echo "→ Changed to $(pwd)"
            fi
        fi
    }
fi
```

**Step 2: Verify syntax**

Run: `bash -n zsh/zshrc` (basic syntax check)
Expected: No errors

**Step 3: Commit**

```bash
git add zsh/zshrc
git commit -m "feat(zsh): add gw wrapper for auto-cd"
```

---

### Task 5: Add shell wrapper to bashrc

**Files:**
- Modify: `bash/bashrc` (after aliases, around line 49)

**Step 1: Add gw wrapper function**

Add after the aliases section (around line 49, before zoxide):

```bash
# gw wrapper - auto-cd after new/rm/cd
if command -v gw &>/dev/null; then
    gw() {
        local output pwd_before
        pwd_before="$PWD"
        output=$(command gw "$@")
        echo "$output"

        # Check last line for "Run: cd ..."
        local last_line cd_path
        last_line=$(echo "$output" | tail -1)
        if [[ "$last_line" == "Run: cd "* ]]; then
            cd_path="${last_line#Run: cd }"
            cd "$cd_path" && echo "→ Changed to $(pwd)"
        # For gw rm: if current directory no longer exists, go to main repo
        elif [[ ! -d "$pwd_before" ]]; then
            local main_repo
            main_repo=$(echo "$output" | grep "Changed to main repo:" | sed 's/.*Changed to main repo: //')
            if [[ -n "$main_repo" && -d "$main_repo" ]]; then
                cd "$main_repo" && echo "→ Changed to $(pwd)"
            fi
        fi
    }
fi
```

**Step 2: Verify syntax**

Run: `bash -n bash/bashrc`
Expected: No errors

**Step 3: Commit**

```bash
git add bash/bashrc
git commit -m "feat(bash): add gw wrapper for auto-cd"
```

---

### Task 6: Test full integration

**Step 1: Create test repo with worktree**

```bash
cd /tmp
git init test-cd
cd test-cd
echo "test" > file.txt
git add file.txt
git commit -m "initial"
git worktree add ../test-cd.feature feature-branch
```

**Step 2: Test gw cd**

Run: `./gw.sh cd` (select the feature worktree)
Expected: Shows picker, prints "Run: cd ../test-cd.feature"

**Step 3: Clean up**

```bash
rm -rf /tmp/test-cd /tmp/test-cd.feature
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(gw): complete shell integration for auto-cd" --allow-empty
```

---

### Task 7: Clean up design docs

**Step 1: Remove plan docs**

```bash
rm -rf docs/plans
git add -A
git commit -m "chore: remove implementation plan docs"
```

---

## Summary

After completing all tasks:

1. `gw cd` command with interactive picker
2. Shell wrapper in zshrc for auto-cd
3. Shell wrapper in bashrc for auto-cd
4. Automatic directory change after `gw new`, `gw cd`, and `gw rm`
