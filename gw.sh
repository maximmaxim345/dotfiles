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

# Get relative path from current dir to target (portable)
get_relative_path() {
    local target="$1"
    local from="${2:-$(pwd)}"
    # Use python for portability (available on both Linux and macOS)
    python3 -c "import os.path; print(os.path.relpath('$target', '$from'))"
}

show_help() {
    cat << 'EOF'
gw - Git Worktree Management Tool

Usage: gw <command> [options]

Commands:
  new       Create a new worktree
  ls, list  List all worktrees with status
  rm, remove Remove a worktree
  cd        Switch to another worktree
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
        cd)
            shift
            cmd_cd "$@"
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
            for default in main master develop dev trunk; do
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
    rel_path=$(get_relative_path "$wt_path")
    echo "Run: cd $rel_path"
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
                echo "  -f, --force  Skip clean check and confirmation for dirty worktrees"
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
    local git_dir
    git_dir=$(git rev-parse --git-dir)
    if [[ "$git_dir" == *"/.git/worktrees/"* ]]; then
        # We're in a worktree - remove current
        wt_to_remove=$(git rev-parse --show-toplevel)
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
            rel_path=$(get_relative_path "$wt_path" "$main_repo")
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

    # Track if we're inside the worktree being removed
    local was_in_worktree=false
    if [[ "$current_dir" == "$wt_to_remove"* ]]; then
        was_in_worktree=true
        cd "$main_repo"
        print_info "Changed to main repo: $main_repo"
    fi

    local git_rm_args=""
    if [[ "$force" == true ]] || [[ "$uncommitted" -gt 0 ]]; then
        git_rm_args="--force"
    fi
    git -C "$main_repo" worktree remove $git_rm_args "$wt_to_remove"

    print_success "Removed worktree at $wt_to_remove"

    # Optionally offer to delete the branch
    if [[ -n "$wt_branch" ]] && [[ "$wt_branch" != "HEAD" ]]; then
        echo -n "Delete branch '$wt_branch'? (yes/Enter to skip): "
        read -r delete_branch
        if [[ "$delete_branch" == "yes" ]]; then
            if git -C "$main_repo" branch -d "$wt_branch" 2>/dev/null; then
                print_success "Deleted branch '$wt_branch'"
            else
                print_warning "Branch '$wt_branch' has unmerged changes"
                echo -n "Force delete? (yes/Enter to skip): "
                read -r force_delete
                if [[ "$force_delete" == "yes" ]]; then
                    git -C "$main_repo" branch -D "$wt_branch"
                    print_success "Force deleted branch '$wt_branch'"
                fi
            fi
        fi
    fi

    # Output cd command for shell wrapper (if we were in the removed worktree)
    if [[ "$was_in_worktree" == true ]]; then
        local rel_path
        rel_path=$(get_relative_path "$main_repo" "$current_dir")
        echo "Run: cd $rel_path"
    fi
}

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
    mkdir -p "$(dirname "$git_exclude")"
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
    if ! command -v "$editor" &>/dev/null; then
        print_error "No suitable editor found. Please set \$EDITOR environment variable."
        exit 1
    fi

    print_info "Opening $setup_script in $editor..."
    "$editor" "$setup_script"

    # Ensure it's still executable after editing
    chmod +x "$setup_script"
    print_success "Setup script saved"
}

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

main "$@"
