# gw Shell Wrapper Design

## Overview

Add shell integration for `gw` to automatically change directory after worktree operations.

**Changes:**
1. Add `gw cd` command with interactive picker (outputs "Run: cd ..." on success)
2. Add shell wrapper function to zsh and bash configs

## `gw cd` Command

Interactive picker to jump between worktrees:

```
$ gw cd
Worktrees:
  1) /home/user/projects/myrepo (main) [main]
  2) /home/user/projects/myrepo.feature-x (feature-x) [clean]
  3) /home/user/projects/refactor/myrepo (refactor-auth) [2 uncommitted]

Switch to which worktree? 2
Run: cd ../myrepo.feature-x
```

- Main repo always listed first with `[main]` indicator
- Shows branch and status like `gw ls`
- Outputs "Run: cd <path>" on last line (same pattern as `gw new`)

## Shell Wrapper Function

Same code for both zsh and bash:

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

**Logic:**
- Captures output, prints it to user
- Parses last line for "Run: cd ..." pattern (works for `gw new` and `gw cd`)
- For `gw rm`: detects if current directory was deleted, parses "Changed to main repo: /path" from output
- Prints "→ Changed to /path" to confirm directory change

## Integration

Add wrapper to:
- `zsh/zshrc` - after aliases/functions section (around line 60)
- `bash/bashrc` - after aliases section

## Compatibility

All commands are portable (macOS + Linux):
- `tail -1`, `head -1`, `awk`, `sed` - standard Unix tools
- `[[ ]]` - bash/zsh (our target shells)
- `${var#pattern}` - standard parameter expansion
