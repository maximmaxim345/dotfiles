-- basic vim configuration
vim.g.mapleader = ' '
vim.opt.signcolumn = 'yes'
vim.opt.wrap = false
vim.opt.linebreak = true
vim.opt.iskeyword:append{'-'}
vim.opt.splitbelow = true
vim.opt.splitright = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 0
vim.opt.expandtab = true
vim.opt.smartindent = true
vim.opt.cmdheight = 1
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.numberwidth = 3
vim.opt.showmode = false
vim.opt.backup = false
vim.opt.writebackup = false
vim.opt.updatetime = 100
vim.opt.timeoutlen = 500
vim.opt.sessionoptions = 'blank,buffers,curdir,help,tabpages,terminal'
vim.opt.mouse = 'a'

if vim.g.vscode then
    -- Very Basic VSCode support
    -- Since some of plugins don't work in vscode, I will not
    -- even bother to load them
    -- Also since the majority of keybindings are not applicable
    -- in vscode, I will recreate them here
    -- Add following to keybindings.json
    --[[
    {
        "command": "vscode-neovim.compositeEscape1",
        "key": "j",
        "when": "neovim.mode == insert && editorTextFocus",
        "args": "j"
    },
    {
        "command": "vscode-neovim.compositeEscape2",
        "key": "k",
        "when": "neovim.mode == insert && editorTextFocus",
        "args": "k"
    }
    ]]
    return
end

-- fix formatoptions
local formatOptions = vim.api.nvim_create_augroup('Format-Options', { clear = true })
vim.api.nvim_create_autocmd("BufEnter", {
    pattern = "*",
    command = "setlocal formatoptions-=c formatoptions-=o",
    group = formatOptions
})
-- set tabstop for various filetypes
vim.api.nvim_create_autocmd("FileType", {
    pattern = {"dart", "javascript", "typescript", "css", "vue", "yaml"},
    command = "setlocal shiftwidth=2 softtabstop=2 expandtab",
    group = formatOptions
})

-- fix barbar in netrw
vim.g.netrw_bufsettings = 'noma nomod nonu nowrap ro buflisted'
if vim.fn.has('termguicolors') == 1 then
    vim.opt.termguicolors = true
end

-- options for neovide
vim.g.neovide_cursor_vfx_mode = 'pixiedust'
vim.g.neovide_cursor_vfx_particle_density = 10.0
vim.g.neovide_fullscreen = false

-- Copilot requires this to be set before loading
vim.g.copilot_no_tab_map = true
vim.g.copilot_assume_mapped = true

vim.filetype.add({extension = {wgsl = 'wgsl'}})

local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({
        "git",
        "clone",
        "--filter=blob:none",
        "https://github.com/folke/lazy.nvim.git",
        "--branch=stable", -- latest stable release
        lazypath,
    })
end
vim.opt.rtp:prepend(lazypath)

-- required for flatten.nvim
-- If opening from inside neovim terminal then do not load all the other plugins
if os.getenv("NVIM") ~= nil then
    require('lazy').setup {
        {
            'willothy/flatten.nvim',
            opts = {},
        },
    }
    return
end

require("lazy").setup({
    {
        'kyazdani42/nvim-web-devicons',
        lazy = true
    },
    {
        'nvim-lua/plenary.nvim',
        lazy = true
    },
    {
        'windwp/nvim-autopairs',
        lazy = true,
        event = 'InsertEnter',
        config = function()
            require"autopairs-cfg"
        end
    },
    {
        'windwp/nvim-ts-autotag',
        lazy = true,
        ft = { 'html', 'javascript', 'javascriptreact', 'typescriptreact', 'svelte', 'vue', 'php', 'xml' },
        config = function()
            require"autotag-cfg"
        end
    },
    {
        'romgrk/barbar.nvim',
        config = function()
            require"barbar-cfg"
        end,
        dependencies = {
            'kyazdani42/nvim-web-devicons',
            'goolord/alpha-nvim',
        }
    },
    {
        'rafamadriz/friendly-snippets',
    },
    {
        'neovim/nvim-lspconfig',
        lazy = true,
        event = { 'InsertEnter', 'CmdLineEnter' },
        config = function()
            require"lsp-cfg"
        end,
        dependencies = {
            {
                "SmiteshP/nvim-navbuddy",
                dependencies = {
                    "SmiteshP/nvim-navic",
                    "MunifTanjim/nui.nvim"
                },
                opts = { lsp = { auto_attach = true } }
            },
            {
                'hrsh7th/nvim-cmp',
            },
            {
                'williamboman/mason-lspconfig.nvim',
            },
            'hrsh7th/cmp-buffer',
            'hrsh7th/cmp-path',
            'hrsh7th/cmp-cmdline',
            'hrsh7th/cmp-calc',
            {
                'petertriho/cmp-git',
                dependencies = {
                    'nvim-lua/plenary.nvim'
                }
            },
            'davidsierradz/cmp-conventionalcommits',
            'hrsh7th/cmp-nvim-lsp-signature-help',
            'hrsh7th/cmp-nvim-lsp-document-symbol',
            'f3fora/cmp-spell',
            -- snippets
            'saadparwaiz1/cmp_luasnip',
            'kyazdani42/nvim-web-devicons',
            {
                'onsails/lspkind-nvim',
            },
            {
                'hrsh7th/cmp-nvim-lsp',
            },
            {
                'L3MON4D3/LuaSnip',
            },
            {
                'nvimdev/lspsaga.nvim',
                dependencies = 'kyazdani42/nvim-web-devicons'
            },
            {
                'jose-elias-alvarez/null-ls.nvim',
                dependencies = {
                    'nvim-lua/plenary.nvim'
                }
            }
        }
    },
    {
        'numToStr/Comment.nvim',
        lazy = true,
        event = 'BufEnter',
        config = function()
            require"comment-cfg"
        end
    },
    {
        'github/copilot.vim',
        lazy = true,
        event = 'BufEnter',
        -- Config is at the top of this file
    },
    {
        'mfussenegger/nvim-dap',
        config = function()
            require"dap-cfg"
        end,
        lazy = true,
        dependencies = {
            'rcarriga/nvim-dap-ui',
            'theHamsta/nvim-dap-virtual-text',
        }
    },
    {
        lazy = true,
        'rcarriga/nvim-dap-ui',
        dependencies = {
            'mfussenegger/nvim-dap',
        }
    },
    {
        "nvim-neotest/neotest",
        dependencies = {
            "nvim-lua/plenary.nvim",
            "nvim-treesitter/nvim-treesitter",
            "antoinemadec/FixCursorHold.nvim",
            "nvim-neotest/neotest-python",
            "sidlatau/neotest-dart",
            "rouge8/neotest-rust"
        },
        lazy = true,
        config = function()
            require"neotest-cfg"
        end,
    },
    {
        'akinsho/flutter-tools.nvim',
        ft = { 'dart' },
        lazy = true,
        config = function()
            require"flutter-cfg"
        end,
        dependencies = {
            'nvim-lua/plenary.nvim',
        }
    },
    {
        'simrat39/rust-tools.nvim',
        config = function()
            local rt = require("rust-tools")
            rt.setup({
              server = {
                on_attach = function(_, bufnr)
                  -- Hover actions
                  vim.keymap.set("n", "<C-space>", rt.hover_actions.hover_actions, { buffer = bufnr })
                end,
              },
            })
        end,
    },
    {
        'lewis6991/gitsigns.nvim',
        config = function()
            require"gitsigns-cfg"
        end
    },
    {
        'ggandor/lightspeed.nvim'
    },
    {
        'williamboman/mason.nvim',
        config = function()
            require"mason-cfg"
        end,
    },
    {
        'hoob3rt/lualine.nvim',
        config = function()
            require"lualine-cfg"
        end,
        dependencies = {
            'arkav/lualine-lsp-progress',
            '1478zhcy/lualine-copilot',
            'kyazdani42/nvim-web-devicons'
        }
    },
    {
        'karb94/neoscroll.nvim',
        config = function() require"neoscroll-cfg" end,
        -- lazy = true,
        cond = not vim.g.neovide -- neovide has its own scrolling
    },
    {
        'kyazdani42/nvim-tree.lua',
        dependencies = {
            'kyazdani42/nvim-web-devicons'
        },
        config = function() require"nvimtree-cfg" end,
        lazy = true,
        cmd = {'NvimTreeToggle'},
    },
    {
        'goolord/alpha-nvim',
        config = function() require"alpha-cfg" end,
    },
    {
        'jedrzejboczar/possession.nvim',
        dependencies = {
            'nvim-lua/plenary.nvim'
        },
        config = function() require"possession-cfg" end,
    },
    {
        'nvim-telescope/telescope.nvim',
        config = function() require"telescope-cfg" end,
        dependencies = {
            'nvim-telescope/telescope-ui-select.nvim',
            'nvim-lua/plenary.nvim',
            'kyazdani42/nvim-web-devicons',
            'debugloop/telescope-undo.nvim',
            'nvim-telescope/telescope-dap.nvim',
            "HUAHUAI23/telescope-dapzzzz"
        }
    },
    {
        'akinsho/nvim-toggleterm.lua',
        config = function() require"toggleterm-cfg" end,
        lazy = true,
        cmd = {'ToggleTerm'},
        keys = {'<M-t>'},
    },
    {
        'nvim-treesitter/nvim-treesitter',
        build = ':TSUpdate',
        config = function() require"treesitter-cfg" end
    },
    {
        'folke/which-key.nvim',
        config = function() require"whichkey-cfg" end
    },
    {
        'tpope/vim-fugitive'
    },
    {
        'TimUntersberger/neogit',
        lazy = true,
        cmd = {'Neogit'},
        dependencies = {
            'nvim-lua/plenary.nvim',
            'sindrets/diffview.nvim'
        },
        config = function()
            require('neogit').setup {
                integrations = {
                    diffview = true
                }
            }
        end
    },
    {
        'lambdalisue/suda.vim',
        lazy = true,
        cmd = {'SudaRead', 'SudaWrite'}
    },
    {
        'NMAC427/guess-indent.nvim',
        config = function()
            require('guess-indent').setup({})
        end
    },
    {
        'folke/trouble.nvim',
        lazy = true,
        cmd = {'TroubleToggle', 'Trouble'},
        dependencies = {
            "kyazdani42/nvim-web-devicons",
            "folke/todo-comments.nvim",
            'neovim/nvim-lspconfig',
        },
        config = function()
            require('todo-comments')
            require('trouble').setup {}
        end
    },
    {
        "folke/todo-comments.nvim",
        dependencies = "nvim-lua/plenary.nvim",
        lazy = true,
        cmd = {'TodoQuickfix', 'TodoTrouble', 'TodoTelescope'},
        config = function()
            require("todo-comments").setup {
            }
        end
    },
    {
        'https://gitlab.com/HiPhish/nvim-ts-rainbow2',
        dependencies = {
            'nvim-treesitter/nvim-treesitter',
        },
        config = function() require"tsrainbow-cfg" end,
    },
    -- {
    --     'kevinhwang91/nvim-hlslens',
    --
    --     config = function() require"hlslens-cfg" end,
    -- },
    {
        'echasnovski/mini.nvim',
        version = false,
        config = function()
            require('mini.indentscope').setup()
            require('mini.trailspace').setup()
            require('mini.bracketed').setup()
        end,
        dependencies = {
            'lewis6991/gitsigns.nvim',
        }
    },
    {
        'Pocco81/true-zen.nvim',
        config = function()
            require("true-zen").setup {
                integrations = {
                    lualine = true,
                }
            }
        end,
    },
    -- {
    --     'j-hui/fidget.nvim',
    --     config = function()
    --         require('fidget').setup()
    --     end
    -- },
    {
        'uga-rosa/ccc.nvim',
        config = function() require"ccc-cfg" end,
    },
    {
        'mg979/vim-visual-multi',
        config = function()
            -- vim.g.VM_mouse_mappings = 1
            vim.g.VM_theme = 'iceblue'
            vim.g.VM_maps = {
                ["Undo"] = "u",
                ["Redo"] = "<C-r>"
            }
        end,
    },
    {
        "danymat/neogen",
        dependencies = "nvim-treesitter/nvim-treesitter",
        lazy = true,
        cmd = {'Neogen'},
        config = function()
            require("neogen").setup({})
        end,
    },
    {
        'asiryk/auto-hlsearch.nvim',
        config = function()
            require('auto-hlsearch').setup()
        end
    },
    {
        'willothy/flatten.nvim',
        -- or pass configuration with
        opts = {  },
        -- Ensure that it runs first to minimize delay when opening file from terminal
        lazy = false, priority = 1001,
    },
    -- {
    --     'm-demare/hlargs.nvim',
    --     dependencies = {
    --         'nvim-treesitter/nvim-treesitter'
    --     },
    --     config = function()
    --         require('hlargs').setup({
    --             color = '#76ea97'
    --         })
    --     end
    -- },
    -- {
    --     'folke/noice.nvim',
    --     config = function()require"noice-cfg" end,
    --     cond = not vim.g.neovide, -- neovide doesn't support noice
    --     dependencies = {
    --         'MunifTanjim/nui.nvim',
    --         'rcarriga/nvim-notify'
    --     }
    -- },
    {
        'nvim-pack/nvim-spectre',
        config = function()
            require('spectre').setup()
        end,
    },
    -- {
    --     "jcdickinson/codeium.nvim",
    --     dependencies = {
    --         "nvim-lua/plenary.nvim",
    --         "hrsh7th/nvim-cmp",
    --     },
    --     config = function()
    --         require("codeium").setup({
    --         })
    --     end
    -- },
    {
        "anuvyklack/windows.nvim",
        dependencies = {
            "anuvyklack/middleclass",
            {
                "anuvyklack/animation.nvim",
                enabled = not vim.g.neovide,
            }
        },
        config = function()
            vim.o.winwidth = 10
            vim.o.winminwidth = 10
            vim.o.equalalways = false
            require('windows').setup{
                ignore = {
                    filetype = { "NvimTree", "neo-tree", "undotree", "gundo", "no-neck-pain" }
                }
            }
        end
    },
    {
        'sindrets/winshift.nvim',
        config = function()
            -- Lua
            require("winshift").setup({
                highlight_moving_win = true,  -- Highlight the window being moved
                focused_hl_group = "Visual",  -- The highlight group used for the moving window
                moving_win_options = {
                    -- These are local options applied to the moving window while it's
                    -- being moved. They are unset when you leave Win-Move mode.
                    wrap = false,
                    cursorline = false,
                    cursorcolumn = false,
                    colorcolumn = "",
                },
                keymaps = {
                    disable_defaults = false, -- Disable the default keymaps
                    win_move_mode = {
                        ["h"] = "left",
                        ["j"] = "down",
                        ["k"] = "up",
                        ["l"] = "right",
                        ["H"] = "far_left",
                        ["J"] = "far_down",
                        ["K"] = "far_up",
                        ["L"] = "far_right",
                        ["<left>"] = "left",
                        ["<down>"] = "down",
                        ["<up>"] = "up",
                        ["<right>"] = "right",
                        ["<S-left>"] = "far_left",
                        ["<S-down>"] = "far_down",
                        ["<S-up>"] = "far_up",
                        ["<S-right>"] = "far_right",
                    },
                },
                ---A function that should prompt the user to select a window.
                ---
                ---The window picker is used to select a window while swapping windows with
                ---`:WinShift swap`.
                ---@return integer? winid # Either the selected window ID, or `nil` to
                ---   indicate that the user cancelled / gave an invalid selection.
                window_picker = function()
                    return require("winshift.lib").pick_window({
                        -- A string of chars used as identifiers by the window picker.
                        picker_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        filter_rules = {
                            -- This table allows you to indicate to the window picker that a window
                            -- should be ignored if its buffer matches any of the following criteria.
                            cur_win = true, -- Filter out the current window
                            floats = true,  -- Filter out floating windows
                            filetype = {},  -- List of ignored file types
                            buftype = {},   -- List of ignored buftypes
                            bufname = {},   -- List of vim regex patterns matching ignored buffer names
                        },
                        ---A function used to filter the list of selectable windows.
                        ---@param winids integer[] # The list of selectable window IDs.
                        ---@return integer[] filtered # The filtered list of window IDs.
                        filter_func = nil,
                    })
                end,
            })
        end,
    },
    {
        'lewis6991/satellite.nvim',
        commit = 'de3b6e70d033a0ddc2d2040fd9e0af76ad16c63e', -- For nvim 0.9
        config = function()
            require('satellite').setup()
        end,
    },
    {
        'shortcuts/no-neck-pain.nvim',
        config = function()
            require('no-neck-pain').setup({
                width = 200,
            })
        end,
    },
    {
        'mbbill/undotree',
    },
    ------------------------------------
    ---            Themes            ---
    ------------------------------------

    {
        'marko-cerovac/material.nvim',
        lazy = true,
    },
    {
        'bluz71/vim-moonfly-colors',
        lazy = true,
    },
    {
        'folke/tokyonight.nvim',
        lazy = true,
    },
    {
        'shaunsingh/nord.nvim',
        lazy = true,
    },
    {
        'projekt0n/github-nvim-theme',
        lazy = true,
    },
    {
        "jesseleite/nvim-noirbuddy",
        lazy = true,
        dependencies = { "tjdevries/colorbuddy.nvim", branch = "dev" }
    },
    {
        'folke/lsp-colors.nvim',
    },
    {
        'uloco/bluloco.nvim',
        dependencies = { 'rktjmp/lush.nvim' },
    },
    {
        'maxmx03/fluoromachine.nvim',
        lazy = true,
    }
})

-- load theme and set keybindings after plugins are loaded
require('theme')
require('keybindings')

-- Create Popup menu
vim.cmd [[
aunmenu PopUp
vnoremenu PopUp.Cut                         "+x
vnoremenu PopUp.Copy                        "+y
anoremenu PopUp.Paste                       "+gP
vnoremenu PopUp.Paste                       "+P
vnoremenu PopUp.Delete                      "_x
nnoremenu PopUp.Select\ All                 ggVG
vnoremenu PopUp.Select\ All                 gg0oG$
inoremenu PopUp.Select\ All                 <C-Home><C-O>VG

anoremenu PopUp.-1-                         <Nop>

" Lsp Options
nnoremenu PopUp.Code\ Action                <Cmd>lua vim.lsp.buf.code_action()<CR>
nnoremenu PopUp.Go\ To\ Definition          <Cmd>Telescope lsp_definitions<CR>
nnoremenu PopUp.Peek\ Definition            <Cmd>Lspsaga peek_definition<CR>
nnoremenu PopUp.Open\ Documentation         <Cmd>Lspsaga hover_doc<CR>
nnoremenu PopUp.Open\ Definitions           <Cmd>Lspsaga finder<CR>
nnoremenu PopUp.Rename\ Symbol              <Cmd>Lspsaga rename<CR>
nnoremenu PopUp.Format\ File                <Cmd>lua vim.lsp.buf.format({async=true})<CR>
nnoremenu PopUp.Toggle\ Workspace\ Diagnostics  <Cmd>TroubleToggle workspace_diagnostics<CR>
nnoremenu PopUp.Diagnostic\ Next            <Cmd>lua vim.lsp.diagnostic.goto_next()<CR>

vnoremenu PopUp.Format\ Range               <Cmd>lua vim.lsp.buf.range_formatting()<CR>

inoremenu PopUp.Code\ Action                <Esc><Cmd>lua vim.lsp.buf.code_action()<CR>
inoremenu PopUp.Go\ To\ Definition          <Esc><Cmd>Telescope lsp_definitions<CR>
inoremenu PopUp.Peek\ Definition            <Esc><Cmd>Lspsaga peek_definition<CR>
inoremenu PopUp.Open\ Documentation         <Esc><Cmd>Lspsaga hover_doc<CR>
inoremenu PopUp.Open\ Definitions           <Esc><Cmd>Lspsaga finder<CR>
inoremenu PopUp.Rename\ Symbol              <Esc><Cmd>Lspsaga rename<CR>
inoremenu PopUp.Format\ File                <Esc><Cmd>lua vim.lsp.buf.format({async=true})<CR>
inoremenu PopUp.Toggle\ Workspace\ Diagnostics  <Esc><Cmd>TroubleToggle workspace_diagnostics<CR>
inoremenu PopUp.Diagnostic\ Next            <Esc><Cmd>lua vim.lsp.diagnostic.goto_next()<CR>

anoremenu PopUp.-2-                         <Nop>

" Buffer Opetions
nnoremenu PopUp.Close\ Buffer               <C-w>c<CR>
nnoremenu PopUp.Split\ Buffer               <C-w>s<CR>
nnoremenu PopUp.Vsplit\ Buffer              <C-w>v<CR>
vnoremenu PopUp.Close\ Buffer               <C-w>c<CR>
vnoremenu PopUp.Split\ Buffer               <C-w>s<CR>
vnoremenu PopUp.Vsplit\ Buffer              <C-w>v<CR>
inoremenu PopUp.Close\ Buffer               <Esc><C-w>c<CR>
inoremenu PopUp.Split\ Buffer               <Esc><C-w>s<CR>
inoremenu PopUp.Vsplit\ Buffer              <Esc><C-w>v<CR>

]]
