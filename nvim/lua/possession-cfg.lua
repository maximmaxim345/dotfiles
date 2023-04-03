vim.api.nvim_create_user_command('SClose',
    function()
        local session = require('possession.session')
        session.autosave()
        session.close()
        vim.api.nvim_command('nohlsearch')
        vim.opt.spell = false
        vim.opt.wrap = false
        vim.g.neovide_fullscreen = false
        theme.set_default()
        require('alpha').start(false)
    end,
    {}
)

require('possession').setup {
    prompt_no_cr = true,
    silent = true,
    autosave = {
        current = true,  -- or fun(name): boolean
        tmp = false,  -- or fun(): boolean
        tmp_name = 'tmp',
        on_load = true,
        on_quit = true,
    },
    commands = {
        save = 'SSave',
        load = 'SLoad', -- open last session
        delete = 'SDelete',
        close = 'PossessionClose',
        show = 'PossessionShow',
        list = 'PossessionList',
        migrate = 'PossessionMigrate',
    },
    hooks = {
        before_save = function(name)
            local user_data = {}
            user_data.font_size = theme.font_size
            user_data.theme = theme.theme_name
            user_data.neovide = {
                fullscreen = vim.g.neovide_fullscreen
            }
            return user_data
        end,
        after_save = function(name, user_data, aborted) end,
        before_load = function(name, user_data)
            -- close all buffers
            vim.api.nvim_command('bufdo bd!')
            if user_data.theme then
                theme.set_theme(user_data.theme)
            end
            if user_data.font_size then
                theme.set_font_size(user_data.font_size, true)
            end
            if user_data.neovide then
                vim.g.neovide_fullscreen = user_data.neovide.fullscreen
            end
            return user_data
        end,
        after_load = function(name, user_data)
            -- reload nvim_tree cwd
            require('nvim-tree.api').tree.change_root(vim.loop.cwd())
        end,
    },
    plugins = {
        close_windows = {
            hooks = {'before_save', 'before_load'},
            preserve_layout = true,  -- or fun(win): boolean
            match = {
                floating = true,
                buftype = {
                    'terminal',
                },
                filetype = {},
                custom = false,  -- or fun(win): boolean
            },
        },
        delete_hidden_buffers = false,
        nvim_tree = true,
        -- tabby = true,
        delete_buffers = false,
    },
}
require('telescope').load_extension('possession')
