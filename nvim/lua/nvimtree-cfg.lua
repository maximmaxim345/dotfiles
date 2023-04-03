-- vim.g.nvim_tree_ignore = {".git", "node_modules", ".cache"}
local tree_cb = require'nvim-tree.config'.nvim_tree_callback
require'nvim-tree'.setup {
    auto_reload_on_write = false,
    disable_netrw = true,
    hijack_netrw = true,
    open_on_setup = false,
    ignore_ft_on_setup = {},
    open_on_tab = true,
    hijack_cursor = true,
    update_cwd = false,
    update_focused_file = {
        enable = false,
        update_cwd = false,
        ignore_list = {}
    },
    filters = {
        dotfiles = false,
    },
    system_open = {
        cmd = nil,
        args = {}
    },
    diagnostics = {
        enable = false,
        show_on_dirs = false,
        icons = {
            hint = "",
            info = "",
            warning = "",
            error = "",
        },
    },
    view = {
        width = 40,
        side = 'left',
        preserve_window_proportions = true,
        mappings = {
            custom_only = true,
            list = {
                { key = "o", cb = tree_cb("edit") },
                { key = "C", cb = tree_cb("cd") },
                -- { key = "v", cb = tree_cb("vsplit") },
                -- { key = "s", cb = tree_cb("split") },
                -- { key = "<C-t>", cb = tree_cb("tabnew") },
                -- { key = "h", cb = tree_cb("close_node") },
                { key = "<BS>", cb = tree_cb("close_node") },
                -- { key = "<S-CR>", cb = tree_cb("close_node") },
                { key = "<Tab>", cb = tree_cb("preview") },
                { key = "H", action = "toggle_ignored" },
                { key = "D", cb = tree_cb("toggle_dotfiles") },
                { key = "R", cb = tree_cb("refresh") },
                { key = "c", cb = tree_cb("create") },
                { key = "d", cb = tree_cb("remove") },
                { key = "r", cb = tree_cb("rename") },
                { key = "<C-r>", cb = tree_cb("full_rename") },
                { key = "x", cb = tree_cb("cut") },
                { key = "y", cb = tree_cb("copy") },
                { key = "p", cb = tree_cb("paste") },
                -- { key = "[c", cb = tree_cb("prev_git_item") },
                -- { key = "]c", cb = tree_cb("next_git_item") },
                { key = ".", cb = tree_cb("dir_up") },
                { key = "q", cb = tree_cb("close") },
                { key = "?", cb = tree_cb("toggle_help") },
            }
        }
    },
    actions = {
        change_dir = {
            global = true
        },
        open_file = {
            quit_on_open = true
        },
    },
    renderer = {
        indent_markers = {
            enable = false,
            icons = {
                corner = "└ ",
                edge = "│ ",
                none = "  ",
            },
        },
        icons = {
            webdev_colors = true,
        },
    },
    git = {
        enable = true,
        ignore = false,
    },
}

vim.g.nvim_tree_icons = {
    default = '',
    symlink = '',
    git = {
        unstaged = "",
        staged = "✓",
        unmerged = "",
        renamed = "➜",
        untracked = "",
        deleted = "",
        ignored = "◌"
    },
    folder = {
        default = "",
        open = "",
        empty = "",
        empty_open = "",
        symlink = ""
    }
}
