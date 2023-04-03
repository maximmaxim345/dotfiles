require('neoscroll').setup({
    mappings = {'<C-y>', '<C-e>', 'zt', 'zz', 'zb'},
    hide_cursor = true,
    stop_eof = true,
    respect_scrolloff = false,
    cursor_scrolls_alone = true,
    easing_function = 'quadratic',
    performance_mode = false,
    time = 100,
})
local t = {}
t["<C-u>"] = { "scroll", { "-vim.wo.scroll", "true", "150" } }
t["<C-d>"] = { "scroll", { "vim.wo.scroll", "true", "150" } }
require'neoscroll.config'.set_mappings(t)
