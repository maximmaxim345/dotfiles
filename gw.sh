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

cmd_remove() {
    print_error "Not implemented yet"
    exit 1
}

cmd_setup() {
    print_error "Not implemented yet"
    exit 1
}

main "$@"
