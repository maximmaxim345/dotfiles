#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
GW_SCRIPT=$(cd -- "$SCRIPT_DIR/.." && pwd)/gw.sh

pass() {
    echo "PASS: $1"
}

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

assert_exists() {
    local path="$1"
    local msg="$2"
    [[ -e "$path" ]] || fail "$msg (missing: $path)"
}

assert_not_exists() {
    local path="$1"
    local msg="$2"
    [[ ! -e "$path" ]] || fail "$msg (unexpected path: $path)"
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="$3"
    [[ "$haystack" == *"$needle"* ]] || fail "$msg (missing '$needle')"
}

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

REPO_PARENT="$TMP_DIR/ws"
REPO="$REPO_PARENT/sample"
mkdir -p "$REPO"

cd "$REPO"
git init -q
git config user.name "test"
git config user.email "test@example.com"
echo "hello" > README.md
git add README.md
git commit -q -m "init"
git branch -M main

# 1) gw new creates new branch worktree from HEAD
new_output=$("$GW_SCRIPT" new -b feat-one --yes --no-prompt)
assert_contains "$new_output" "GW_CD_TARGET=" "gw new should emit machine-readable cd target"
WT_ONE="$REPO_PARENT/sample.feat-one"
assert_exists "$WT_ONE" "gw new should create sibling worktree"

# 2) gw new from subdirectory still uses repo root
mkdir -p "$REPO/src/nested"
cd "$REPO/src/nested"
"$GW_SCRIPT" new -b feat-two --yes --no-prompt >/dev/null
WT_TWO="$REPO_PARENT/sample.feat-two"
assert_exists "$WT_TWO" "gw new from subdir should still create sibling worktree"

# 3) gw move moves branch out of main worktree
cd "$REPO"
git checkout -q -b move-me
echo "move" >> README.md
git add README.md
git commit -q -m "move branch commit"
move_output=$("$GW_SCRIPT" move --yes --no-prompt)
assert_contains "$move_output" "GW_CD_TARGET=" "gw move should emit machine-readable cd target"
WT_MOVE="$REPO_PARENT/sample.move-me"
assert_exists "$WT_MOVE" "gw move should create branch worktree"
current_main_branch=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
[[ "$current_main_branch" == "main" ]] || fail "gw move should switch main worktree back to main"

# 4) gw ls --json handles detached worktree entries
git -C "$REPO" worktree add --detach "$REPO_PARENT/sample.detached" >/dev/null
ls_json=$("$GW_SCRIPT" ls --json)
assert_contains "$ls_json" '"detached": true' "gw ls --json should report detached worktree"

# 5) gw cd --index emits cd target
cd_output=$("$GW_SCRIPT" cd --index 1)
assert_contains "$cd_output" "GW_CD_TARGET=" "gw cd --index should emit cd target"

# 6) gw rm --path works non-interactively
"$GW_SCRIPT" rm --path "$WT_TWO" --yes --no-prompt >/dev/null
assert_not_exists "$WT_TWO" "gw rm --path should remove target worktree"

# 7) prune/doctor smoke
"$GW_SCRIPT" prune >/dev/null
"$GW_SCRIPT" doctor >/dev/null

pass "gw workflow tests"
