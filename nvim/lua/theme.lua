-- enable material.nvim theme on startup
vim.g.material_style = "palenight"

theme = {}

require('material').setup({
    plugins = {
        "dap",
        "dashboard",
        "gitsigns",
        "hop",
        "lspsaga",
        "nvim-cmp",
        "nvim-tree",
        "sneak",
        "telescope",
    },
    lualine_style = "stealth",
})

function theme.set_theme(theme_name)
    -- test if beginns with material
    if string.match(theme_name, "material ") then
        vim.g.material_style = string.sub(theme_name, 10)
        vim.cmd('colorscheme material')
    elseif string.match(theme_name, "noirbuddy ") then
        local preset = string.sub(theme_name, 11)
        require('noirbuddy').setup {
            preset = preset,
        }
    else
        vim.cmd('colorscheme ' .. theme_name)
    end
    theme.theme_name = theme_name
end

-- open telescope with a list of all themes (including material.nvim variations)
function theme.open_theme_list()
    local themes = {
		"material darker",
		"material lighter",
		"material deep ocean",
		"material oceanic",
		"material palenight",
        "noirbuddy minimal",
        "noirbuddy miami-nights",
        "noirbuddy kiwi",
        "noirbuddy slate",
        "noirbuddy crt-green",
        "noirbuddy crt-amber",
        "moonfly",
        "github_light",
        "github_dark",
        "github_dimmed",
        "tokyonight",
        "nord"}
    local opts = {
        scroll_strategy = "cycle",
        layout_strategy = "center",
        initial_mode = "insert", -- normal
        previewer = false,
    }
    local bufnr = vim.api.nvim_get_current_buf()
    local p = vim.api.nvim_buf_get_name(bufnr)
    local picker = require("telescope.pickers").new(opts, {
        results_title = "Themes",
        prompt_title = "Select a theme",
        finder = require("telescope.finders").new_table {
            results = themes,
        },
        sorter = require("telescope.config").values.generic_sorter(opts),
        attach_mappings = function(prompt_bufnr, map)
            -- map default actions
            require("telescope.actions").select_default:replace(function()
                local selection = require("telescope.actions.state").get_selected_entry()
                theme.set_theme(selection.value)
                require("telescope.actions").close(prompt_bufnr)
            end)
            return true
        end,
    })
    picker:find()
end

-- function to change font size
theme.font_size = 0
function theme.set_font_size(size, absolute)
    if absolute then
        theme.font_size = size
    else
        theme.font_size = theme.font_size + size
    end
    -- minimum font size
    if theme.font_size <= 3 then
        theme.font_size = 3
    end
    vim.opt.guifont = {
        'Fira_Code_Light:h'..theme.font_size,
        'Iosevka_Light:h'..theme.font_size,
    }
end
-- set default font size and theme
function theme.set_default()
    theme.set_font_size(14, true)
    theme.set_theme('material palenight')
end
theme.set_default()
