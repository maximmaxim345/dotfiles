local cmp = require'cmp'

require("mason-lspconfig").setup()

local lspconfig = require("lspconfig")
local capabilities = require('cmp_nvim_lsp').default_capabilities()
capabilities.offsetEncoding = 'utf-8' -- Needed for clangd
capabilities.textDocument.completion.completionItem.snippetSupport = true

require("mason-lspconfig").setup_handlers({
    function (server_name)
        -- default handler for all other servers
        require("lspconfig")[server_name].setup {
            capabilities = capabilities,
        }
    end,
    ["clangd"] = function ()
        lspconfig.clangd.setup {
            opts = {
                cmd = { "clangd", "--completion-style=detailed",
                    "--limit-results=3000"
                }
            },
            capabilities = capabilities,
        }
    end,
    -- ["sumneko_lua"] = function ()
    --     lspconfig.sumneko_lua.setup {
    --         settings = {
    --             Lua = {
    --                 diagnostics = {
    --                     globals = { "vim" }
    --                 }
    --             }
    --         }
    --     }
    -- end,
    ["omnisharp"] = function ()
        lspconfig.omnisharp.setup {
            capabilities = capabilities,
        }
    end,
    ["pylsp"] = function ()
        lspconfig.pylsp.setup {
            settings = {
                pylsp = {
                    plugins = {
                        pycodestyle = {
                            ignore = {'W391'},
                            maxLineLength = 100
                        }
                    }
                }
            }
        }
    end,
})

local luasnip = require("luasnip")
require("luasnip.loaders.from_vscode").lazy_load()
local has_words_before = function()
  local line, col = unpack(vim.api.nvim_win_get_cursor(0))
  return col ~= 0 and vim.api.nvim_buf_get_lines(0, line - 1, line, true)[1]:sub(col, col):match("%s") == nil
end

cmp.setup({
    window = {
        completion = cmp.config.window.bordered(),
        documentation = cmp.config.window.bordered(),
    },
    formatting = {
        format = require('lspkind').cmp_format({
            mode = 'symbol',
            maxwidth = 70,
            ellipsis_char = '...',

            -- The function below will be called before any actual modifications from lspkind
            -- so that you can provide more controls on popup customization. (See [#30](https://github.com/onsails/lspkind-nvim/pull/30))
            before = function (entry, vim_item)
                return vim_item
            end,
            symbol_map = { Codeium = "", }
        })
    },
    snippet = {
        expand = function(args)
            luasnip.lsp_expand(args.body)
        end,
    },
    mapping = {
        ['<C-b>'] = cmp.mapping.scroll_docs(-4),
        ['<C-f>'] = cmp.mapping.scroll_docs(4),
        ["<Tab>"] = cmp.mapping(function(fallback)
            if cmp.visible() then
                cmp.select_next_item()
            elseif luasnip.expand_or_jumpable() then
                luasnip.expand_or_jump()
            -- elseif has_words_before() then
            --     cmp.complete()
            else
                fallback()
            end
        end, { "i", "s" }),

        ["<S-Tab>"] = cmp.mapping(function(fallback)
            if cmp.visible() then
                cmp.select_prev_item()
            elseif luasnip.jumpable(-1) then
                luasnip.jump(-1)
            else
                fallback()
            end
        end, { "i", "s" }),
        ['<C-Space>'] = cmp.mapping(function(fallback)
            if cmp.visible() then
                local entry = cmp.get_active_entry()
                if entry and entry.source == 'luasnip' then
                    print('luasnip')
                    cmp.confirm({
                        behavior = cmp.ConfirmBehavior.Replace, -- or Insert
                        select = true,
                    })
                else
                    cmp.confirm({
                        select = true,
                    })
                end
            elseif luasnip.expand_or_jumpable() then
                luasnip.expand_or_jump()
            else
                cmp.complete({
                    config = {
                        preselect = cmp.PreselectMode.Item,
                    }
                })
            end
        end, { 'i', 'c' }),
    },
    sources = cmp.config.sources(
        {
            -- { name = 'codeium', priority = 4 },
            { name = 'calc', priority = 2 },
            { name = 'luasnip', priority = 1},
            { name = 'nvim_lsp', priority = 2},
            { name = 'nvim_lsp_signature_help', priority = 3},
            { name = 'spell', priority = 1},
        },
        {
            { name = 'buffer' },
        }
    ),
    completion = {
        keyword_length = 2,
    }
})

cmp.setup.filetype('gitcommit', {
    sources = cmp.config.sources({
        { name = 'conventionalcommits' },
        { name = 'cmp_git' },
    }, {
        { name = 'buffer' },
    })
})
-- Setup compleation for search and command mode
cmp.setup.cmdline('/', {
    sources = cmp.config.sources {
        { name = 'nvim_lsp_document_symbol' },
        { name = 'buffer' }
    }
})
cmp.setup.cmdline('?', {
    sources = cmp.config.sources {
        { name = 'nvim_lsp_document_symbol' },
        { name = 'buffer' }
    }
})
cmp.setup.cmdline(':', {
    sources = cmp.config.sources {
        { name = 'path' },
        { name = 'cmdline' }
    }
})

local cmp_autopairs = require('nvim-autopairs.completion.cmp')
cmp.event:on(
  'confirm_done',
  cmp_autopairs.on_confirm_done()
)

require('lspsaga').setup({})

local null_ls = require('null-ls')
local mreg = require('mason-registry')
local function add_if_installed(package_name, source)
    if mreg.is_installed(package_name) then
        return source
    end
    return nil
end
null_ls.setup({
    sources = {
        null_ls.builtins.diagnostics.todo_comments,
        -- null_ls.builtins.diagnostics.trail_space,
        null_ls.builtins.hover.dictionary,
        -- add_if_installed('eslint_d', null_ls.builtins.code_actions.eslint_d),
        add_if_installed('eslint_d', null_ls.builtins.diagnostics.eslint_d),
        add_if_installed('eslint_d', null_ls.builtins.formatting.eslint_d),
        add_if_installed('prettierd', null_ls.builtins.formatting.prettierd),
        add_if_installed('luaformatter', null_ls.builtins.formatting.lua_format),
        -- add_if_installed('', null_ls.builtins.formatting.json_tool),
        add_if_installed('cmakelang', null_ls.builtins.formatting.cmake_format),
        add_if_installed('cmakelang', null_ls.builtins.diagnostics.cmake_lint),
        add_if_installed('clang-format', null_ls.builtins.formatting.clang_format),
        add_if_installed('yamllint', null_ls.builtins.diagnostics.yamllint),
        add_if_installed('yamlfmt', null_ls.builtins.formatting.yamlfmt),
        -- add_if_installed('', null_ls.builtins.diagnostics.gccdiag)
    }
})
