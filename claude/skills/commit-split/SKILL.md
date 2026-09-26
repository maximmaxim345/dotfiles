Split uncommitted changes into multiple logical commits using `git add -p`.

Follow @~/.claude/commit-guidelines.md for commit message format.

Compose each commit message inline. Do not delegate to a subagent. For the subagent variant use `/commit-split-subagent`.

## Workflow

### 1. Analyze Changes
Run these commands to understand current state:
- `git status` - overall state
- `git diff HEAD` - all changes (staged + unstaged)

Parse the diff output. Each `@@` marker indicates a hunk boundary.

### 2. Group Hunks into Commits
Identify logical groupings based on:
- Related functionality (same feature/fix)
- File type (tests should go with their implementation)
- Dependencies (hunks that depend on each other)

### 3. Present Plan
Show the user a numbered list of proposed commits:
```
Proposed commits:
1. fix: handle null user in login
   - src/auth.ts: lines 45-52 (null check)
2. refactor: simplify logout flow
   - src/auth.ts: lines 78-95 (logout logic)
   - src/auth.test.ts: lines 30-45 (tests)
3. chore(deps): update axios
   - package.json: line 12
```

Ask the user to confirm before proceeding.

### 4. Execute Each Commit
For each commit group, in order:

1. Reset staging: `git reset HEAD` (if anything staged)
2. Stage selected hunks using `git add -p` with piped y/n responses:
   ```bash
   printf 'y\nn\ny\n' | git add -p
   ```
   Each y/n corresponds to a hunk in order - 'y' to stage, 'n' to skip.
3. Commit: `git commit -m "message"`

### 5. Verify
After all commits:
- `git log --oneline -N` (where N = number of commits created)
- `git status` to confirm working directory is clean

## Important Notes

- Track hunk order carefully - `git add -p` presents hunks in a specific order
- If a hunk depends on another, they must be in the same commit
- Use conventional commit types: `fix:`, `feat:`, `refactor:`, `chore:`, `docs:`, `test:`, `perf:`
