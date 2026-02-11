#!/bin/bash
set -euo pipefail

# gw - Git Worktree Management Tool

VERSION="2.0.0"

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

emit_cd_target() {
    local target="$1"
    echo "GW_CD_TARGET=${target}"
}

# Get relative path from current dir to target (portable)
get_relative_path() {
    local target="$1"
    local from="${2:-$(pwd)}"
    # Use python for portability (available on both Linux and macOS)
    python3 -c "import os.path; print(os.path.relpath('$target', '$from'))"
}

show_help() {
    cat << 'EOF_HELP'
gw - Git Worktree Management Tool

Usage: gw <command> [options]

Commands:
  new       Create a new worktree with a new branch
  move      Move current branch to a new worktree
  ls, list  List all worktrees with status
  rm, remove Remove a worktree
  cd        Switch to another worktree
  prune     Prune stale worktree metadata
  doctor    Validate worktree setup and health
  setup     Edit the worktree setup script for this repo

Options:
  -h, --help     Show this help message
  -v, --version  Show version

Examples:
  gw new -b feature-x         # Create new branch worktree from HEAD
  gw new -b feature-x --from main
  gw move                     # Move current branch into a worktree
  gw ls                       # List all worktrees
  gw rm                       # Remove current worktree (if in one)
  gw cd                       # Pick and switch worktree
EOF_HELP
}

require_arg() {
    local flag="$1"
    local value="${2:-}"
    if [[ -z "$value" || "$value" == -* ]]; then
        print_error "Missing value for $flag"
        exit 1
    fi
}

# Get the main repo directory (works from worktree, main repo, or subdirs)
get_main_repo() {
    local git_common_dir
    git_common_dir=$(git rev-parse --git-common-dir)

    # Normalize to absolute path when git returns a relative path.
    if [[ "$git_common_dir" != /* ]]; then
        git_common_dir="$(cd "$git_common_dir" && pwd -P)"
    fi

    dirname "$git_common_dir"
}

# Check if we're in a git repo
require_git_repo() {
    if ! git rev-parse --git-dir &>/dev/null; then
        print_error "Not in a git repository"
        exit 1
    fi
}

sanitize_branch_for_path() {
    echo "$1" | tr '/' '-'
}

is_worktree_clean() {
    local repo_path="$1"
    [[ -z "$(git -C "$repo_path" status --porcelain 2>/dev/null)" ]]
}

resolve_default_branch() {
    local main_repo="$1"
    local resolved

    resolved=$(git -C "$main_repo" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*/||' || true)
    if [[ -n "$resolved" ]]; then
        echo "$resolved"
        return 0
    fi

    for default in main master develop dev trunk; do
        if git -C "$main_repo" show-ref --verify --quiet "refs/heads/$default"; then
            echo "$default"
            return 0
        fi
    done

    return 1
}

branch_display_name() {
    local branch_ref="$1"
    local detached="$2"

    if [[ "$detached" == "true" ]]; then
        echo "DETACHED"
        return 0
    fi

    if [[ -z "$branch_ref" ]]; then
        echo "UNKNOWN"
        return 0
    fi

    if [[ "$branch_ref" == refs/heads/* ]]; then
        echo "${branch_ref#refs/heads/}"
        return 0
    fi

    echo "$branch_ref"
}

# Print unit-separator separated:
# path<US>head<US>branch_ref<US>detached<US>locked<US>prunable
iter_worktrees() {
    local main_repo="$1"

    local path=""
    local head=""
    local branch_ref=""
    local detached="false"
    local locked="false"
    local prunable="false"

    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]]; then
            if [[ -n "$path" ]]; then
                printf '%s\x1f%s\x1f%s\x1f%s\x1f%s\x1f%s\n' "$path" "$head" "$branch_ref" "$detached" "$locked" "$prunable"
            fi
            path=""
            head=""
            branch_ref=""
            detached="false"
            locked="false"
            prunable="false"
            continue
        fi

        case "$line" in
            worktree\ *)
                path="${line#worktree }"
                ;;
            HEAD\ *)
                head="${line#HEAD }"
                ;;
            branch\ *)
                branch_ref="${line#branch }"
                ;;
            detached)
                detached="true"
                ;;
            locked*)
                locked="true"
                ;;
            prunable*)
                prunable="true"
                ;;
        esac
    done < <(git -C "$main_repo" worktree list --porcelain; echo)
}

build_worktree_path() {
    local main_repo="$1"
    local repo_name="$2"
    local branch_name="$3"
    local subfolder="$4"

    local parent_dir
    parent_dir=$(dirname "$main_repo")

    if [[ -n "$subfolder" ]]; then
        echo "$parent_dir/$subfolder/$repo_name"
    else
        local safe_branch
        safe_branch=$(sanitize_branch_for_path "$branch_name")
        echo "$parent_dir/$repo_name.$safe_branch"
    fi
}

pick_worktree() {
    local allow_main="$1"
    local prompt="$2"
    local no_prompt="$3"
    local main_repo="$4"

    PICKED_WORKTREE=""

    local worktrees=()
    local labels=()

    while IFS=$'\x1f' read -r wt_path wt_head wt_branch_ref wt_detached wt_locked wt_prunable; do
        [[ -z "$wt_path" ]] && continue

        if [[ "$allow_main" != "true" && "$wt_path" == "$main_repo" ]]; then
            continue
        fi

        worktrees+=("$wt_path")

        local branch_name uncommitted status_str rel_path is_main=""
        branch_name=$(branch_display_name "$wt_branch_ref" "$wt_detached")
        uncommitted=$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

        if [[ "$uncommitted" -gt 0 ]]; then
            status_str="[${uncommitted} uncommitted]"
        else
            status_str="[clean]"
        fi

        if [[ "$wt_path" == "$main_repo" ]]; then
            is_main=" [main]"
        fi

        rel_path=$(get_relative_path "$wt_path" "$(pwd)")
        labels+=("$rel_path ($branch_name)$is_main $status_str")
    done < <(iter_worktrees "$main_repo")

    if [[ ${#worktrees[@]} -eq 0 ]]; then
        print_info "No worktrees found"
        return 1
    fi

    local selected=""

    if [[ "$no_prompt" == "true" ]]; then
        print_error "Selection required in non-interactive mode"
        return 1
    fi

    if [[ -t 0 && -t 1 ]] && command -v fzf &>/dev/null; then
        local fzf_input
        fzf_input=$(printf '%s\n' "${labels[@]}")
        selected=$(printf '%s\n' "$fzf_input" | fzf --prompt "$prompt " --height 40% --reverse --border || true)
        if [[ -z "$selected" ]]; then
            print_info "Cancelled"
            return 1
        fi

        local idx
        for idx in "${!labels[@]}"; do
            if [[ "${labels[$idx]}" == "$selected" ]]; then
                PICKED_WORKTREE="${worktrees[$idx]}"
                return 0
            fi
        done

        print_error "Failed to resolve selection"
        return 1
    fi

    echo "Worktrees:"
    local i
    for i in "${!labels[@]}"; do
        echo "  $((i+1))) ${labels[$i]}"
    done
    echo ""

    echo -n "$prompt "
    local choice
    read -r choice

    if [[ -z "$choice" ]]; then
        print_info "Cancelled"
        return 1
    fi

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 ]] || [[ "$choice" -gt ${#worktrees[@]} ]]; then
        print_error "Invalid selection"
        return 1
    fi

    PICKED_WORKTREE="${worktrees[$((choice-1))]}"
    return 0
}

run_setup_script_if_present() {
    local main_repo="$1"
    local wt_path="$2"
    local setup_script="$main_repo/.worktree-setup.sh"

    if [[ -x "$setup_script" ]]; then
        print_info "Running setup script..."
        if ! (cd "$wt_path" && "$setup_script"); then
            print_warning "Setup script failed (exit code $?), but worktree was created"
        fi
    fi
}

cmd_new() {
    require_git_repo

    local branch=""
    local subfolder=""
    local base_ref="HEAD"
    local no_prompt="false"
    local yes="false"
    local do_fetch="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -b|--branch)
                require_arg "$1" "${2:-}"
                branch="$2"
                shift 2
                ;;
            --from)
                require_arg "$1" "${2:-}"
                base_ref="$2"
                shift 2
                ;;
            -s|--subfolder)
                require_arg "$1" "${2:-}"
                subfolder="$2"
                shift 2
                ;;
            --yes)
                yes="true"
                shift
                ;;
            --no-prompt)
                no_prompt="true"
                shift
                ;;
            --fetch)
                do_fetch="true"
                shift
                ;;
            -h|--help)
                echo "Usage: gw new [-b <branch>] [--from <ref>] [-s <subfolder>] [--fetch] [--yes] [--no-prompt]"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    local main_repo repo_name
    main_repo=$(get_main_repo)
    repo_name=$(basename "$main_repo")

    if [[ "$do_fetch" == "true" ]]; then
        print_info "Fetching remotes..."
        git -C "$main_repo" fetch --all --prune
    fi

    if [[ -z "$branch" ]]; then
        if [[ "$no_prompt" == "true" ]]; then
            print_error "Branch name is required when --no-prompt is used (pass -b/--branch)"
            exit 1
        fi
        echo -n "New branch name: "
        read -r branch
        if [[ -z "$branch" ]]; then
            print_error "Branch name cannot be empty"
            exit 1
        fi
    fi

    if [[ -z "$subfolder" && "$no_prompt" != "true" ]]; then
        echo -n "Subfolder (empty for sibling directory): "
        read -r subfolder
    fi

    if ! git -C "$main_repo" rev-parse --verify "$base_ref^{commit}" &>/dev/null; then
        print_error "Base ref does not resolve to a commit: $base_ref"
        exit 1
    fi

    if git -C "$main_repo" show-ref --verify --quiet "refs/heads/$branch"; then
        print_error "Branch already exists: $branch"
        exit 1
    fi

    local wt_path
    wt_path=$(build_worktree_path "$main_repo" "$repo_name" "$branch" "$subfolder")

    if [[ -e "$wt_path" ]]; then
        print_error "Path already exists: $wt_path"
        exit 1
    fi

    if [[ "$yes" != "true" && "$no_prompt" != "true" ]]; then
        echo -n "Create worktree at '$wt_path' from '$base_ref'? (yes/Enter to cancel): "
        local confirm
        read -r confirm
        if [[ "$confirm" != "yes" ]]; then
            print_info "Cancelled"
            exit 0
        fi
    elif [[ "$no_prompt" == "true" && "$yes" != "true" ]]; then
        print_error "Use --yes with --no-prompt for non-interactive creation"
        exit 1
    fi

    mkdir -p "$(dirname "$wt_path")"

    print_info "Creating worktree with new branch '$branch' (from '$base_ref')..."
    git -C "$main_repo" worktree add -b "$branch" "$wt_path" "$base_ref"

    run_setup_script_if_present "$main_repo" "$wt_path"

    echo ""
    print_success "Created worktree at $wt_path"

    local rel_path
    rel_path=$(get_relative_path "$wt_path")
    emit_cd_target "$rel_path"
}

cmd_move() {
    require_git_repo

    local subfolder=""
    local explicit_path=""
    local no_prompt="false"
    local yes="false"
    local do_fetch="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -s|--subfolder)
                require_arg "$1" "${2:-}"
                subfolder="$2"
                shift 2
                ;;
            --to)
                require_arg "$1" "${2:-}"
                explicit_path="$2"
                shift 2
                ;;
            --yes)
                yes="true"
                shift
                ;;
            --no-prompt)
                no_prompt="true"
                shift
                ;;
            --fetch)
                do_fetch="true"
                shift
                ;;
            -h|--help)
                echo "Usage: gw move [-s <subfolder>] [--to <path>] [--fetch] [--yes] [--no-prompt]"
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

    if [[ "$current_branch" == "HEAD" ]]; then
        print_error "Cannot move detached HEAD to a worktree"
        exit 1
    fi

    if [[ "$do_fetch" == "true" ]]; then
        print_info "Fetching remotes..."
        git -C "$main_repo" fetch --all --prune
    fi

    # Check if branch is already checked out in another worktree
    while IFS=$'\x1f' read -r wt_path wt_head wt_branch_ref wt_detached wt_locked wt_prunable; do
        [[ -z "$wt_path" ]] && continue
        if [[ "$wt_branch_ref" == "refs/heads/$current_branch" && "$wt_path" != "$main_repo" ]]; then
            print_error "Branch '$current_branch' is already checked out in another worktree: $wt_path"
            exit 1
        fi
    done < <(iter_worktrees "$main_repo")

    upstream_branch=$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null | sed 's|.*/||' || true)
    if [[ -z "$upstream_branch" ]]; then
        upstream_branch=$(resolve_default_branch "$main_repo" || true)
    fi

    if [[ -z "$upstream_branch" ]]; then
        print_error "Cannot determine upstream/default branch to switch main repo to"
        exit 1
    fi

    if [[ "$current_branch" == "$upstream_branch" ]]; then
        print_error "Cannot move '$current_branch' to worktree - it's the upstream/default branch"
        exit 1
    fi

    if ! is_worktree_clean "$main_repo"; then
        print_error "Main worktree has uncommitted changes; commit/stash before running gw move"
        exit 1
    fi

    local wt_path
    if [[ -n "$explicit_path" ]]; then
        wt_path="$explicit_path"
    else
        if [[ -z "$subfolder" && "$no_prompt" != "true" ]]; then
            echo -n "Subfolder (empty for sibling directory): "
            read -r subfolder
        fi
        wt_path=$(build_worktree_path "$main_repo" "$repo_name" "$current_branch" "$subfolder")
    fi

    if [[ -e "$wt_path" ]]; then
        print_error "Path already exists: $wt_path"
        exit 1
    fi

    if [[ "$yes" != "true" && "$no_prompt" != "true" ]]; then
        echo -n "Move branch '$current_branch' to '$wt_path'? (yes/Enter to cancel): "
        local confirm
        read -r confirm
        if [[ "$confirm" != "yes" ]]; then
            print_info "Cancelled"
            exit 0
        fi
    elif [[ "$no_prompt" == "true" && "$yes" != "true" ]]; then
        print_error "Use --yes with --no-prompt for non-interactive move"
        exit 1
    fi

    mkdir -p "$(dirname "$wt_path")"

    print_info "Switching main repo to '$upstream_branch'..."
    git -C "$main_repo" checkout "$upstream_branch"

    print_info "Creating worktree with branch '$current_branch'..."
    git -C "$main_repo" worktree add "$wt_path" "$current_branch"

    run_setup_script_if_present "$main_repo" "$wt_path"

    echo ""
    print_success "Moved branch '$current_branch' to worktree at $wt_path"

    local rel_path
    rel_path=$(get_relative_path "$wt_path")
    emit_cd_target "$rel_path"
}

cmd_list() {
    require_git_repo

    local as_json="false"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --json)
                as_json="true"
                shift
                ;;
            -h|--help)
                echo "Usage: gw ls [--json]"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    local main_repo
    main_repo=$(get_main_repo)

    local first_json_item="true"
    if [[ "$as_json" == "true" ]]; then
        echo "["
    fi

    while IFS=$'\x1f' read -r wt_path wt_head wt_branch_ref wt_detached wt_locked wt_prunable; do
        [[ -z "$wt_path" ]] && continue

        local branch_name is_main="false"
        branch_name=$(branch_display_name "$wt_branch_ref" "$wt_detached")
        if [[ "$wt_path" == "$main_repo" ]]; then
            is_main="true"
        fi

        local status_parts=()
        local uncommitted
        uncommitted=$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        if [[ "$uncommitted" -gt 0 ]]; then
            status_parts+=("${uncommitted} uncommitted")
        fi

        local upstream
        upstream=$(git -C "$wt_path" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
        local ahead=0
        local behind=0
        if [[ -n "$upstream" ]]; then
            ahead=$(git -C "$wt_path" rev-list --count '@{upstream}..HEAD' 2>/dev/null || echo "0")
            behind=$(git -C "$wt_path" rev-list --count 'HEAD..@{upstream}' 2>/dev/null || echo "0")
            if [[ "$ahead" -gt 0 ]]; then
                status_parts+=("${ahead} ahead")
            fi
            if [[ "$behind" -gt 0 ]]; then
                status_parts+=("${behind} behind")
            fi
        fi

        local status_str=""
        if [[ ${#status_parts[@]} -eq 0 ]]; then
            status_str="clean"
        else
            status_str="$(IFS=', '; echo "${status_parts[*]}")"
        fi

        if [[ "$as_json" == "true" ]]; then
            local json_path json_branch json_status
            json_path=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$wt_path")
            json_branch=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$branch_name")
            json_status=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$status_str")

            if [[ "$first_json_item" != "true" ]]; then
                echo ","
            fi
            first_json_item="false"
            printf '  {"path": %s, "branch": %s, "is_main": %s, "status": %s, "detached": %s, "locked": %s, "prunable": %s}' \
                "$json_path" "$json_branch" "$is_main" "$json_status" "$wt_detached" "$wt_locked" "$wt_prunable"
        else
            local status_print is_main_tag=""
            if [[ "$is_main" == "true" ]]; then
                is_main_tag=" [main]"
            fi
            status_print="[$status_str]"
            echo -e "${wt_path} ${BLUE}(${branch_name})${NC}${is_main_tag} ${status_print}"
        fi
    done < <(iter_worktrees "$main_repo")

    if [[ "$as_json" == "true" ]]; then
        echo ""
        echo "]"
    fi
}

cmd_remove() {
    require_git_repo

    local main_repo current_dir
    main_repo=$(get_main_repo)
    current_dir=$(pwd)

    local force="false"
    local explicit_path=""
    local yes="false"
    local no_prompt="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--force)
                force="true"
                shift
                ;;
            --path)
                require_arg "$1" "${2:-}"
                explicit_path="$2"
                shift 2
                ;;
            --yes)
                yes="true"
                shift
                ;;
            --no-prompt)
                no_prompt="true"
                shift
                ;;
            -h|--help)
                echo "Usage: gw rm [-f|--force] [--path <worktree>] [--yes] [--no-prompt]"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    local wt_to_remove=""

    if [[ -n "$explicit_path" ]]; then
        wt_to_remove="$explicit_path"
    else
        local git_dir
        git_dir=$(git rev-parse --git-dir)
        if [[ "$git_dir" == *"/.git/worktrees/"* ]]; then
            wt_to_remove=$(git rev-parse --show-toplevel)
        else
            pick_worktree "false" "Remove which worktree?" "$no_prompt" "$main_repo" || exit 1
            wt_to_remove="$PICKED_WORKTREE"
        fi
    fi

    if [[ "$wt_to_remove" == "$main_repo" ]]; then
        print_error "Refusing to remove main worktree"
        exit 1
    fi

    local uncommitted
    uncommitted=$(git -C "$wt_to_remove" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$uncommitted" -gt 0 ]] && [[ "$force" != "true" ]]; then
        if [[ "$yes" == "true" ]]; then
            force="true"
        elif [[ "$no_prompt" == "true" ]]; then
            print_error "Worktree has uncommitted changes; use --force or --yes"
            exit 1
        else
            print_warning "Worktree has $uncommitted uncommitted changes!"
            echo ""
            git -C "$wt_to_remove" status --short
            echo ""
            echo -n "Type 'yes' to force delete: "
            local confirm
            read -r confirm
            if [[ "$confirm" != "yes" ]]; then
                print_info "Cancelled"
                exit 0
            fi
            force="true"
        fi
    fi

    local wt_branch
    wt_branch=$(git -C "$wt_to_remove" rev-parse --abbrev-ref HEAD 2>/dev/null || true)

    print_info "Removing worktree at $wt_to_remove..."

    local was_in_worktree="false"
    if [[ "$current_dir" == "$wt_to_remove"* ]]; then
        was_in_worktree="true"
        cd "$main_repo"
        print_info "Changed to main repo: $main_repo"
    fi

    if [[ "$force" == "true" ]]; then
        git -C "$main_repo" worktree remove --force "$wt_to_remove"
    else
        git -C "$main_repo" worktree remove "$wt_to_remove"
    fi

    print_success "Removed worktree at $wt_to_remove"

    if [[ "$no_prompt" != "true" ]]; then
        if [[ -n "$wt_branch" ]] && [[ "$wt_branch" != "HEAD" ]]; then
            echo -n "Delete branch '$wt_branch'? (yes/Enter to skip): "
            local delete_branch
            read -r delete_branch
            if [[ "$delete_branch" == "yes" ]]; then
                if git -C "$main_repo" branch -d "$wt_branch" 2>/dev/null; then
                    print_success "Deleted branch '$wt_branch'"
                else
                    print_warning "Branch '$wt_branch' has unmerged changes"
                    echo -n "Force delete? (yes/Enter to skip): "
                    local force_delete
                    read -r force_delete
                    if [[ "$force_delete" == "yes" ]]; then
                        git -C "$main_repo" branch -D "$wt_branch"
                        print_success "Force deleted branch '$wt_branch'"
                    fi
                fi
            fi
        fi
    fi

    if [[ "$was_in_worktree" == "true" ]]; then
        local rel_path
        rel_path=$(get_relative_path "$main_repo" "$current_dir")
        emit_cd_target "$rel_path"
    fi
}

cmd_setup() {
    require_git_repo

    local main_repo
    main_repo=$(get_main_repo)

    local setup_script="$main_repo/.worktree-setup.sh"
    local git_exclude="$main_repo/.git/info/exclude"

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

    mkdir -p "$(dirname "$git_exclude")"
    if ! grep -qF '.worktree-setup.sh' "$git_exclude" 2>/dev/null; then
        echo '.worktree-setup.sh' >> "$git_exclude"
        print_info "Added .worktree-setup.sh to .git/info/exclude"
    fi

    chmod +x "$setup_script"

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

    chmod +x "$setup_script"
    print_success "Setup script saved"
}

cmd_cd() {
    require_git_repo

    local explicit_path=""
    local explicit_index=""
    local no_prompt="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --path)
                require_arg "$1" "${2:-}"
                explicit_path="$2"
                shift 2
                ;;
            --index)
                require_arg "$1" "${2:-}"
                explicit_index="$2"
                shift 2
                ;;
            --no-prompt)
                no_prompt="true"
                shift
                ;;
            -h|--help)
                echo "Usage: gw cd [--path <worktree>] [--index <n>] [--no-prompt]"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    local main_repo
    main_repo=$(get_main_repo)

    if [[ -n "$explicit_path" ]]; then
        local rel_path
        rel_path=$(get_relative_path "$explicit_path" "$(pwd)")
        emit_cd_target "$rel_path"
        return 0
    fi

    if [[ -n "$explicit_index" ]]; then
        if ! [[ "$explicit_index" =~ ^[0-9]+$ ]]; then
            print_error "--index must be a positive integer"
            exit 1
        fi

        local worktrees=()
        while IFS=$'\x1f' read -r wt_path wt_head wt_branch_ref wt_detached wt_locked wt_prunable; do
            [[ -z "$wt_path" ]] && continue
            worktrees+=("$wt_path")
        done < <(iter_worktrees "$main_repo")

        if [[ "$explicit_index" -lt 1 ]] || [[ "$explicit_index" -gt ${#worktrees[@]} ]]; then
            print_error "Index out of range"
            exit 1
        fi

        local selected_path rel_path
        selected_path="${worktrees[$((explicit_index-1))]}"
        rel_path=$(get_relative_path "$selected_path" "$(pwd)")
        emit_cd_target "$rel_path"
        return 0
    fi

    pick_worktree "true" "Switch to which worktree?" "$no_prompt" "$main_repo" || exit 1
    local selected_path
    selected_path="$PICKED_WORKTREE"

    local rel_path
    rel_path=$(get_relative_path "$selected_path" "$(pwd)")
    emit_cd_target "$rel_path"
}

cmd_prune() {
    require_git_repo

    local main_repo
    main_repo=$(get_main_repo)

    local before after
    before=$(git -C "$main_repo" worktree list --porcelain | grep -c '^worktree ' || true)

    print_info "Pruning stale worktree metadata..."
    git -C "$main_repo" worktree prune

    after=$(git -C "$main_repo" worktree list --porcelain | grep -c '^worktree ' || true)

    print_success "Prune complete"
    echo "Worktrees before: $before"
    echo "Worktrees now:    $after"
}

cmd_doctor() {
    require_git_repo

    local main_repo
    main_repo=$(get_main_repo)

    local issues=0

    local setup_script="$main_repo/.worktree-setup.sh"
    if [[ -f "$setup_script" && ! -x "$setup_script" ]]; then
        print_warning "setup script exists but is not executable: $setup_script"
        issues=$((issues+1))
    fi

    while IFS=$'\x1f' read -r wt_path wt_head wt_branch_ref wt_detached wt_locked wt_prunable; do
        [[ -z "$wt_path" ]] && continue

        if [[ ! -d "$wt_path" ]]; then
            print_warning "missing worktree path: $wt_path"
            issues=$((issues+1))
            continue
        fi

        if ! git -C "$wt_path" rev-parse --git-dir &>/dev/null; then
            print_warning "invalid git worktree: $wt_path"
            issues=$((issues+1))
            continue
        fi

        if [[ "$wt_prunable" == "true" ]]; then
            print_warning "worktree marked prunable: $wt_path"
            issues=$((issues+1))
        fi

        if [[ "$wt_detached" != "true" ]]; then
            local upstream
            upstream=$(git -C "$wt_path" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
            local branch_name
            branch_name=$(branch_display_name "$wt_branch_ref" "$wt_detached")
            if [[ -z "$upstream" ]]; then
                print_warning "branch has no upstream ($branch_name): $wt_path"
            fi
        fi
    done < <(iter_worktrees "$main_repo")

    if [[ "$issues" -eq 0 ]]; then
        print_success "Doctor: no hard issues found"
        return 0
    fi

    print_error "Doctor found $issues issue(s)"
    return 1
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
        move)
            shift
            cmd_move "$@"
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
        prune)
            shift
            cmd_prune "$@"
            ;;
        doctor)
            shift
            cmd_doctor "$@"
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

main "$@"
