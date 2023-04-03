local alpha = require('alpha')
local dashboard = require('alpha.themes.dashboard')

dashboard.section.header.val = {
    [[                          __        ]],
    [[   ____  ___  ____ _   __/_/___ ___ ]],
    [[  / __ \/ _ \/ __ \ | / / / __ `__ \]],
    [[ / / / /  __/ /_/ / |/ / / / / / / /]],
    [[/_/ /_/\___/\____/|___/_/_/ /_/ /_/ ]],
    [[                                    ]]
}
dashboard.section.buttons.val = {
    dashboard.button( "s", "Search a session" , ":Telescope possession list<CR>"),
    dashboard.button( "o", "New file" , ":ene<CR>"),
    dashboard.button( "f", "Find file" , ":Telescope find_files<CR>"),
    dashboard.button( "g", "Find word" , ":Telescope live_grep<CR>"),
    dashboard.button( "t", "Change theme" , ":lua theme.open_theme_list()<CR>"),
    dashboard.button( "l", "Open Lazy", ":Lazy<CR>"),
    dashboard.button( "m", "Open Mason", ":Mason<CR>"),
    dashboard.button( "q", "Quit NVIM" , ":qa<CR>"),
}
alpha.setup(dashboard.config)
