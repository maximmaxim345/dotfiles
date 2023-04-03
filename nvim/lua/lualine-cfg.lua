local function session_name()
    return require('possession.session').session_name or ''
end

require('lualine').setup {
    options = {
        theme = 'auto',
        globalstatus = true,
    },
    sections = {
        lualine_a = {'mode'},
        lualine_b = {'branch', 'diff', 'diagnostics' },
        lualine_c = {'filename'},
        lualine_x = {'copilot', 'encoding', 'fileformat', 'filetype', {
            require("lazy.status").updates,
            cond = require("lazy.status").has_updates,
            color = { fg = "#ff9e64" },
        },},
        lualine_y = {'progress'},
        lualine_z = { session_name }
    },
    extensions = {'nvim-tree', 'toggleterm'}
}
