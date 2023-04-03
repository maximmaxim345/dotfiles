require'gitsigns'.setup
{
    on_attach = function(bufnr)
        keybindings.gitsigns(bufnr)
    end,
    watch_gitdir = {
        interval = 1000
    },
    current_line_blame = false,
    sign_priority = 6,
    update_debounce = 100,
    status_formatter = nil, -- Use default
}
