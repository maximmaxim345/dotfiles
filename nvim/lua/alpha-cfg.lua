local alpha = require('alpha')
local dashboard = require('alpha.themes.dashboard')

M = {}

dashboard.section.header.val = {
    [[                          __        ]],
    [[   ____  ___  ____ _   __/_/___ ___ ]],
    [[  / __ \/ _ \/ __ \ | / / / __ `__ \]],
    [[ / / / /  __/ /_/ / |/ / / / / / / /]],
    [[/_/ /_/\___/\____/|___/_/_/ /_/ /_/ ]],
    [[                                    ]]
}

function M.alpha_load_buttons()
    local last_session_button = {}
    local session = require("possession")
    local last_session = session.last()
    if last_session~= nil then
        -- we have a last session, just use the filename without the extension
        last_session =  string.match(last_session, "([^/\\]+)%.json$")
        local button = dashboard.button( "<leader><leader>", "Open " .. last_session, ":SLoad<CR>")
        table.insert(last_session_button, button)
    end
    dashboard.section.buttons.val = {
        dashboard.button( "s", "Search a session" , ":Telescope possession list<CR>"),
        table.unpack(last_session_button),
        dashboard.button( "o", "New file" , ":ene<CR>"),
        dashboard.button( "f", "Find file" , ":Telescope find_files<CR>"),
        dashboard.button( "g", "Find word" , ":Telescope live_grep<CR>"),
        dashboard.button( "t", "Change theme" , ":lua theme.open_theme_list()<CR>"),
        dashboard.button( "l", "Open Lazy (package manager)", ":Lazy<CR>"),
        dashboard.button( "m", "Open Mason (LSP/DAP/Linters)", ":Mason<CR>"),
        dashboard.button( "q", "Quit NVIM" , ":qa<CR>"),
    }
end

M.alpha_load_buttons()
alpha.setup(dashboard.config)
return M
