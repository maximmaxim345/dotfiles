-- vim.g.nvim_tree_ignore = {".git", "node_modules", ".cache"}
require'nvim-tree'.setup {
    auto_reload_on_write = false,
    disable_netrw = true,
    hijack_netrw = true,
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
        -- mappings = {
        --     custom_only = true,
        --     list = {
        --         { key = "o", cb = tree_cb("edit") },
        --         { key = "C", cb = tree_cb("cd") },
        --         -- { key = "v", cb = tree_cb("vsplit") },
        --         -- { key = "s", cb = tree_cb("split") },
        --         -- { key = "<C-t>", cb = tree_cb("tabnew") },
        --         -- { key = "h", cb = tree_cb("close_node") },
        --         { key = "<BS>", cb = tree_cb("close_node") },
        --         -- { key = "<S-CR>", cb = tree_cb("close_node") },
        --         { key = "<Tab>", cb = tree_cb("preview") },
        --         { key = "H", action = "toggle_ignored" },
        --         { key = "D", cb = tree_cb("toggle_dotfiles") },
        --         { key = "R", cb = tree_cb("refresh") },
        --         { key = "c", cb = tree_cb("create") },
        --         { key = "d", cb = tree_cb("remove") },
        --         { key = "r", cb = tree_cb("rename") },
        --         { key = "<C-r>", cb = tree_cb("full_rename") },
        --         { key = "x", cb = tree_cb("cut") },
        --         { key = "y", cb = tree_cb("copy") },
        --         { key = "p", cb = tree_cb("paste") },
        --         -- { key = "[c", cb = tree_cb("prev_git_item") },
        --         -- { key = "]c", cb = tree_cb("next_git_item") },
        --         { key = ".", cb = tree_cb("dir_up") },
        --         { key = "q", cb = tree_cb("close") },
        --         { key = "?", cb = tree_cb("toggle_help") },
        --     }
        -- }
    },
    on_attach = function(bufnr)
        local api = require('nvim-tree.api')
        local function opts(desc)
            return { desc = 'nvim-tree: ' .. desc, buffer = bufnr, noremap = true, silent = true, nowait = true }
        end
        local function remove_keymap(key)
            -- Add incase it's not already set
            vim.keymap.set('n', key, '', { buffer = bufnr})
            vim.keymap.del('n', key, { buffer = bufnr})
        end

        api.config.mappings.default_on_attach(bufnr)

        vim.keymap.set('n', '<C-e>', api.node.open.replace_tree_buffer,     opts('Open: In Place'))
        vim.keymap.set('n', '<C-k>', api.node.show_info_popup,              opts('Info'))
        vim.keymap.set('n', '<C-r>', api.fs.rename_sub,                     opts('Rename: Omit Filename'))
        vim.keymap.set('n', '<C-t>', api.node.open.tab,                     opts('Open: New Tab'))
        vim.keymap.set('n', '<C-v>', api.node.open.vertical,                opts('Open: Vertical Split'))
        vim.keymap.set('n', '<C-x>', api.node.open.horizontal,              opts('Open: Horizontal Split'))
        vim.keymap.set('n', '<BS>',  api.node.navigate.parent_close,        opts('Close Directory'))
        vim.keymap.set('n', '<CR>',  api.node.open.edit,                    opts('Open'))
        vim.keymap.set('n', '<Tab>', api.node.open.preview,                 opts('Open Preview'))
        vim.keymap.set('n', '>',     api.node.navigate.sibling.next,        opts('Next Sibling'))
        vim.keymap.set('n', '<',     api.node.navigate.sibling.prev,        opts('Previous Sibling'))
        vim.keymap.set('n', '.',     api.node.run.cmd,                      opts('Run Command'))
        vim.keymap.set('n', 'bmv',   api.marks.bulk.move,                   opts('Move Bookmarked'))
        vim.keymap.set('n', 'B',     api.tree.toggle_no_buffer_filter,      opts('Toggle No Buffer'))
        vim.keymap.set('n', 'd',     api.fs.remove,                         opts('Delete'))
        vim.keymap.set('n', 'D',     api.fs.trash,                          opts('Trash'))
        vim.keymap.set('n', 'E',     api.tree.expand_all,                   opts('Expand All'))
        vim.keymap.set('n', 'e',     api.fs.rename_basename,                opts('Rename: Basename'))
        vim.keymap.set('n', ']e',    api.node.navigate.diagnostics.next,    opts('Next Diagnostic'))
        vim.keymap.set('n', '[e',    api.node.navigate.diagnostics.prev,    opts('Prev Diagnostic'))
        vim.keymap.set('n', 'F',     api.live_filter.clear,                 opts('Clean Filter'))
        vim.keymap.set('n', 'f',     api.live_filter.start,                 opts('Filter'))
        vim.keymap.set('n', 'gy',    api.fs.copy.absolute_path,             opts('Copy Absolute Path'))
        vim.keymap.set('n', 'J',     api.node.navigate.sibling.last,        opts('Last Sibling'))
        vim.keymap.set('n', 'K',     api.node.navigate.sibling.first,       opts('First Sibling'))
        vim.keymap.set('n', 'm',     api.marks.toggle,                      opts('Toggle Bookmark'))
        vim.keymap.set('n', 'o',     api.node.open.edit,                    opts('Open'))
        vim.keymap.set('n', 'O',     api.node.open.no_window_picker,        opts('Open: No Window Picker'))
        vim.keymap.set('n', 'p',     api.fs.paste,                          opts('Paste'))
        vim.keymap.set('n', 'P',     api.node.navigate.parent,              opts('Parent Directory'))
        vim.keymap.set('n', 'q',     api.tree.close,                        opts('Close'))
        vim.keymap.set('n', 'r',     api.fs.rename,                         opts('Rename'))
        vim.keymap.set('n', 'R',     api.tree.reload,                       opts('Refresh'))
        vim.keymap.set('n', 's',     api.node.run.system,                   opts('Run System'))
        vim.keymap.set('n', 'S',     api.tree.search_node,                  opts('Search'))
        vim.keymap.set('n', 'U',     api.tree.toggle_custom_filter,         opts('Toggle Hidden'))
        vim.keymap.set('n', 'W',     api.tree.collapse_all,                 opts('Collapse'))
        vim.keymap.set('n', 'x',     api.fs.cut,                            opts('Cut'))
        vim.keymap.set('n', 'y',     api.fs.copy.filename,                  opts('Copy Name'))
        vim.keymap.set('n', 'Y',     api.fs.copy.relative_path,             opts('Copy Relative Path'))
        vim.keymap.set('n', '<2-LeftMouse>',  api.node.open.edit,           opts('Open'))
        vim.keymap.set('n', '<2-RightMouse>', api.tree.change_root_to_node, opts('CD'))

        remove_keymap('g?')
        vim.keymap.set('n', '?',     api.tree.toggle_help,                  opts('Help'))
        vim.keymap.set('n', 'C', api.tree.change_root_to_node,          opts('CD'))
        vim.keymap.set('n', 'gi',     api.tree.toggle_gitignore_filter,      opts('Toggle Git Ignore'))
        vim.keymap.set('n', 'gc',     api.tree.toggle_git_clean_filter,      opts('Toggle Git Clean'))
        vim.keymap.set('n', 'gN',    api.node.navigate.git.prev,            opts('Prev Git'))
        vim.keymap.set('n', 'gn',    api.node.navigate.git.next,            opts('Next Git'))
        vim.keymap.set('n', 'H',     api.tree.toggle_hidden_filter,         opts('Toggle Dotfiles'))
        remove_keymap('c')
        vim.keymap.set('n', 'y',     api.fs.copy.node,                      opts('Copy'))
        vim.keymap.set('n', 'c',     api.fs.create,                         opts('Create'))
        remove_keymap('.')
        vim.keymap.set('n', '.',     api.tree.change_root_to_parent,        opts('Up'))
    end,
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
