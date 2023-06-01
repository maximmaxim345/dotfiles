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

            local map = require('mini.map')
            map.setup({
                integrations = {
                    map.gen_integration.diagnostic({
                        error = 'DiagnosticFloatingError',
                        warn  = 'DiagnosticFloatingWarn',
                        info  = 'DiagnosticFloatingInfo',
                        hint  = 'DiagnosticFloatingHint',
                    }),
                    map.gen_integration.builtin_search({}),
                    map.gen_integration.gitsigns({}),
                }
            })
        end,
        dependencies = {
            'lewis6991/gitsigns.nvim',
        }
    },
    {
        'folke/twilight.nvim',
        lazy = true,
        cmd = {'Twilight'},
        config = function() require"twilight-cfg" end,
    },
    {
        'folke/zen-mode.nvim',
        lazy = true,
        cmd = {'ZenMode'},
        dependencies = {
            'folke/twilight.nvim',
        },
        config = function()
            require('zen-mode').setup({})
        end
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
})

-- load theme and set keybindings after plugins are loaded
require('theme')
require('keybindings')
