local wk = require('which-key')

if vim.g.neovide then
    vim.api.nvim_set_keymap('n', '<Leader>+', ':lua theme.set_font_size(1)<CR>', {noremap = true, silent = true, desc = "Increase Font size" })
    vim.api.nvim_set_keymap('n', '<Leader>-', ':lua theme.set_font_size(-1)<CR>', {noremap = true, silent = true, desc = "Decrease Font size" })
    vim.api.nvim_set_keymap('n', '<F11>', ':lua vim.g.neovide_fullscreen = not vim.g.neovide_fullscreen<CR>', {noremap = true, silent = true, desc = "Toggle Fullscreen" })
else

    wk.register({
        ['<leader>N'] = {
            name = "Neoscroll",
            p = { ':NeoscrollEnableGlobalPM<CR>', 'Enable performance mode' },
            P = { ':NeoscrollDisableGlobalPM<CR>', 'Disable performance mode' },
        }
    }, {
        mode = 'n',
    })
end

vim.api.nvim_set_keymap("i", "jk", "<Esc>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("i", "<C-BS>", "<C-W>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("i", "<S-Tab>", "<C-d>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("t", "jk", "<C-\\><C-n>", { noremap = true, silent = true })

wk.register({
    ['<C-s>'] = { ':w<CR>', 'Save file' },
    -- Buffer management
    ['<TAB>'] = { ':BufferNext<CR>', 'Focus next buffer' },
    ['<S-TAB>'] = { ':BufferPrevious<CR>', 'Focus previous buffer' },
    ['<c-q>'] = { ':BufferClose<CR>', 'Close the current buffer' },
    -- LSP
    K = { ':Lspsaga hover_doc<CR>', 'Show documentation (LSP)' },

    ['<M-t>'] = 'Toggle terminal (can be prefixed with terminal number)', -- set in toggleterm-cfg
    -- Navigation
    ['<M-j>'] = { ':resize -2<CR>', 'Decrease window height' },
    ['<M-k>'] = { ':resize +2<CR>', 'Increase window height' },
    ['<M-h>'] = { ':vertical resize -2<CR>', 'Decrease window width' },
    ['<M-l>'] = { ':vertical resize +2<CR>', 'Increase window width' },
    ['<C-h>'] = { '<C-w>h', 'Go to the left window' },
    ['<C-j>'] = { '<C-w>j', 'Go to the bottom window' },
    ['<C-k>'] = { '<C-w>k', 'Go to the top window' },
    ['<C-l>'] = { '<C-w>l', 'Go to the right window' },
    s = 'search below cursor (lightspeed)', -- set by lightspeed
    S = 'search above cursor (lightspeed)', -- set by lightspeed
    ['<C-w>'] = {
        ['<c-m>'] = { ':WindowsMaximize<CR>', 'Maximize window' },
        ['<c-v>'] = { ':WindowsMaximizeVertically<CR>', 'Maximize window vertically' },
        ['<c-h>'] = { ':WindowsMaximizeHorizontally<CR>', 'Maximize window horizontally' },
        ['<c-e>'] = { ':WindowsEqualize<CR>', 'Equalize windows' },
        ['<c-w>'] = { ':WinShift<CR>', 'Move Window' },
        ['<c-s>'] = { ':WinShift swap<CR>', 'Swap Window' },
        ['<c-t>'] = { ':WindowsToggleAutowidth<CR>', 'Toggle autowidth' },
    },
    ['<leader>'] = {
        name = 'More commands',
        -- More buffer management
        ['<c-q>'] = { ':BufferClose!<CR>', 'Close buffer forcefully' },
        ['<S-TAB>'] = { ':BufferMovePrevious<CR>', 'Move buffer to left' },
        ['<TAB>'] = { ':BufferMoveNext<CR>', 'Move buffer to right' },

        t = { ':NvimTreeToggle<CR>', 'Toggle file explorer (nvim-tree)' },
        T = { ':NvimTreeFindFile<CR>', 'Select the current file in file explorer (nvim-tree)' },
        b = {
            name = 'BarBar',
            ['<Up>'] = { ':BufferPick<CR>', 'Pick a buffer (BarBar)' },
            ['d'] = { ':BufferOrderByDirectory<CR>', 'Sort buffers by directory' },
            ['l'] = { ':BufferOrderByLanguage<CR>', 'Sort buffers by language' },
            ['p'] = { ':BufferPin<CR>', 'Pin/Unpin a buffer' },
            ['r'] = { ':BufferRestore<CR>', 'Restore the last closed buffer' },
        },
        c = {
            name = 'Copilot',
            e = { ':Copilot enable<CR>', 'Enable copilot' },
            d = { ':Copilot disable<CR>', 'Disable copilot' },
            f = {
                name = 'File specific settings',
                e = { ':let b:copilot_enabled=v:true<CR>', 'Enable copilot for the current file' },
                d = { ':let b:copilot_enabled=v:false<CR>', 'Disable copilot for the current file' },
            },
        },
        C = { ':CccPick<CR>', 'Open colorpicker (ccc)' },
        p = { ':Lspsaga diagnostic_jump_prev<CR>', 'Go to previous diagnostic (LSP)' },
        n = { ':Lspsaga diagnostic_jump_next<CR>', 'Go to next diagnostic (LSP)' },
        l = {
            name = 'LSP',
            l = { ':Navbuddy<CR>', 'Open Navbuddy (LSP)' },
            a = { ':lua vim.lsp.buf.code_action()<CR>', 'Code action' },
            d = { ':Telescope lsp_definitions<CR>', 'Go to definition' },
            D = { ':Lspsaga peek_definition<CR>', 'Peek definition' },
            K = { ':Lspsaga hover_doc<CR>', 'Open documentation' },
            k = { ':Lspsaga finder<CR>', 'Open definitions/implementations/references' },
            r = { ':Lspsaga rename<CR>', 'Rename symbol' },
            h = { ':ClangdSwitchSourceHeader<CR>', 'Switch between header and source file (Clangd)' },
            f = { ':lua vim.lsp.buf.format({async=true})<CR>', 'Format file' },
            F = { ':Telescope flutter commands<CR>', 'Open flutter commands' },
            L = { ':TroubleToggle workspace_diagnostics<CR>', 'Toggle workspace diagnostics list' },
            I = { ':LspInfo<CR>', 'Show LSP info' },
            t = { ':TroubleToggle todo<CR>', 'Toggle todo list' },
            T = {
                name = 'Run tests',
                r = { ':lua require("neotest").run.run()<CR>', 'Run nearest test' },
                R = { ':lua require("neotest").run.run({strategy = "dap"})<CR>', 'Run nearest test with debugging' },
                f = { ':lua require("neotest").run.run(vim.fn.expand("%"))<CR>', 'Run all tests in current file' },
                F = { ':lua require("neotest").run.run({vim.fn.expand("%"), strategy = "dap"})<CR>', 'Run all tests in current file with debugging' },
                x = { ':lua require("neotest").run.stop()<CR>', 'Stop running tests' },
                T = { ':lua require("neotest").output_panel.toggle()<CR>', 'Toggle test output' },
            },
            g = { ':Neogen<CR>', 'Generate documentation' },
        },
        d = {
            name = 'Debug',
            u = { ':lua require"dapui".toggle()<CR>', 'Toggle DAP UI' },
            b = { ':lua require"dap".toggle_breakpoint()<CR>', 'Toggle breakpoint' },
            c = { ':lua require"dap".continue()<CR>', 'Continue or start debugging' },
            l = { ':lua require"dap".run_last()<CR>', 'Rerun last debug session' },
            o = { ':lua require"dap".step_over()<CR>', 'Step over' },
            i = { ':lua require"dap".step_into()<CR>', 'Step into' },
            O = { ':lua require"dap".step_out()<CR>', 'Step out' },
            x = { ':lua require"dap".disconnect()<CR>:lua require"dap".close()<CR>', 'Disconnect and close debugger' },
            X = { ':lua require"dap".terminate()<CR>', 'Terminate application and close debugger' },
            d = { ':Telescope dap commands<CR>', 'Open list of DAP commands' },
        },
        ['.'] = { ":lua theme.open_theme_list()<CR>", 'Change theme' },
        f = {
            name = 'Find/Spectre',
            f = { ':Telescope find_files<CR>', 'Find files' },
            g = { ':Telescope live_grep<CR>', 'Find word' },
            b = { ':Telescope buffers<CR>', 'Find buffers' },
            h = { ':Telescope help_tags<CR>', 'Find help (neovim)' },
            m = { ':Telescope man_pages<CR>', 'Find help (man pages)' },
            u = { ':Telescope undo<CR>', 'Find undo history' },
            s = { ':lua require"spectre".open()<CR>', 'Open Spectre' },
            w = { ':lua require"spectre".open_visual({select_word=true})<CR>', 'Search for current word' },
        },
        I = { ':GuessIndent', 'Guess the indentation of the current file' },
        z = {
            name = 'Zen/NoNeckPain',
            n = { ':TZNarrow<CR>', 'Narrow' },
            f = { ':TZFocus<CR>', 'Focus' },
            m = { ':TZMinimalist<CR>', 'Minimalist' },
            a = { ':TZAtaraxis<CR>', 'Ataraxis (Zen)' },
            z = { ':NoNeckPain<CR>', 'NoNeckPain' },
        },
        s = {
            name = 'Sessions',
            c = { ':SClose<CR>', 'Close current session' },
            l = { ':Telescope possession list<CR>', 'Load a session' },
            q = { ':SQuit<CR>', 'Quit' },
        },
        g = {
            name = 'Git',
            g = { ':Neogit<CR>', 'Open Neogit' },
        },
        q = { ':SQuit<CR>', 'Quit' },
        u = { ':UndotreeToggle<CR>', 'Toggle undo tree' },
    },
    -- hide neoscroll keybindings
    ['<C-y>'] = 'which_key_ignore',
    ['<C-e>'] = 'which_key_ignore',
    ['<C-u>'] = 'which_key_ignore',
    ['<C-d>'] = 'which_key_ignore',
    zt = 'which_key_ignore',
    zz = 'which_key_ignore',
    zb = 'which_key_ignore',
    gd = { ':Lspsaga lsp_finder<CR>', 'Open definitions/implementations/references' },
}, {
    mode = 'n',
})

wk.register({
    ['<C-s>'] = { '<C-O>:w<CR>', 'Save file' },
    -- Copilot
    ['<M-c>'] = {
        name = 'Copilot',
        ['<M-c>'] = { 'copilot#Accept("")', 'Accept copilot suggestion', expr = true },
        n = { '<Plug>(copilot-next)', 'Next copilot suggestion', noremap = false },
        p = { '<Plug>(copilot-previous)', 'Previous copilot suggestion', noremap = false },
        ['<ESC>'] = { '<Plug>(copilot-dismiss)', 'Dismiss copilot suggestion', noremap = false },
        -- space
        ['<Space>'] = { '<ESC>:Copilot panel<CR>', 'Open copilot panel' },
    },
}, {
    mode = 'i',
})
wk.register({
    ['>'] = { '>gv', 'indent right' },
    ['<'] = { '<gv', 'indent left' },
    ['<leader>'] = {
        name = 'More commands',
        l = {
            name = 'LSP',
            a = { ':lua vim.lsp.buf.range_code_action()<CR>', 'Code action' },
            f = { ':lua vim.lsp.buf.range_formatting()<CR>', 'Format range' },
        },
        z = {
            name = 'Zen',
            n = { ":'<,'>TZNarrow<CR>", 'Narrow' },
        },
        s = { ':lua require("spectre").open()<CR>', 'Open search and replace' },
        f = {
            name = 'Find/Spectre',
            w = { '<esc><cmd>lua require("spectre").open_visual()<CR>', 'Search for current word' },
        },
    }
}, {
    mode = 'v',
})

-- Macros for bettter markdown/LaTeX editing (for qwertz keyboard layout)
vim.api.nvim_set_keymap("i", "jt", "$$<ESC>i", {})
vim.api.nvim_set_keymap("i", "jT", "$$<CR>$$<ESC>O", {})
vim.api.nvim_set_keymap("i", "jß", "\\", {})
vim.api.nvim_set_keymap("i", "jö", "\\", {})
vim.api.nvim_set_keymap("i", "j7", "{", {})
vim.api.nvim_set_keymap("i", "j0", "}", {})
vim.api.nvim_set_keymap("i", "jc", "`", {})
vim.api.nvim_set_keymap("i", "jC", "```", {})
vim.api.nvim_set_keymap("i", "jB", "\\{\\}<ESC>hi", {})

-- Keybinding bound to local buffers or lazy-loaded plugins

keybindings = {}

keybindings.gitsigns = function(bufnr)
    wk.register({
        ['<leader>'] = {
            g = {
                n = { "&diff ? ']c' : ':lua require\"gitsigns\".next_hunk()<CR>'", 'Go to next hunk in file', expr = true },
                N = { "&diff ? '[c' : ':lua require\"gitsigns\".prev_hunk()<CR>'", 'Go to previous hunk in file', expr = true },
                s = { ':lua require"gitsigns".stage_hunk()<CR>', 'Add hunk to stage' },
                u = { ':lua require"gitsigns".undo_stage_hunk()<CR>', 'Undo last add hunk' },
                r = { ':lua require"gitsigns".reset_hunk()<CR>', 'Reset hunk' },
                R = { ':lua require"gitsigns".reset_buffer()<CR>', 'Reset the whole buffer' },
                p = { ':lua require"gitsigns".preview_hunk_inline()<CR>', 'Preview changes in hunk' },
                b = { ':lua require"gitsigns".blame_line()<CR>', 'Run git blame on the current line' },
                d = { ':lua require"gitsigns".diffthis()<CR>', 'Open diff against the current index' },
                S = {
                    name = 'Git signs options',
                    w = { ':lua require"gitsigns".toggle_word_diff()<CR>', 'Toggle word diff' },
                    d = { ':lua require"gitsigns".toggle_deleted()<CR>', 'Toggle show deleted' },
                    b = { ':lua require"gitsigns".toggle_current_line_blame()<CR>', 'Toggle current line blame' },
                },
            }
        }
    }, {
        mode = 'n',
        buffer = bufnr,
    })
end
