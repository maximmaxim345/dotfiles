local gears = require("gears")
local awful = require("awful")
local wibox = require("wibox")
local beautiful = require("beautiful")
local naughty = require("naughty")
local menubar = require("menubar")
local hotkeys_popup = require("awful.hotkeys_popup")

local o = {}

o.setup = function()
    editor = os.getenv("EDITOR") or "nvim"
    editor_cmd = settings.terminal .. " -e " .. editor

    modkey = "Mod4"

    awful.layout.layouts = {
        awful.layout.suit.floating,
        awful.layout.suit.tile,
        awful.layout.suit.tile.top,
        awful.layout.suit.magnifier,
    }

    menubar.utils.terminal = settings.terminal -- Set the terminal for applications that require it

    require("components.lines.client")

    awful.screen.connect_for_each_screen(function(s)
        gears.wallpaper.maximized(beautiful.wallpaper, s)
        s:connect_signal("property::geometry", function()
            gears.wallpaper.maximized(beautiful.wallpaper)
        end)
        -- awful.tag({ "1", "2", "3", "4", "5", "6", "7", "8", "9" }, s, awful.layout.suit.tile)
        local config_dir = gears.filesystem.get_configuration_dir()
        local icon_dir = config_dir .. "/icons/lines/"
        for i=1,7 do
            awful.tag.add(i, {
                screen = s,
                selected = i == 1,
                layout = awful.layout.suit.tile,
            })
        end
        local function update_tag_icons()
            for i, t in ipairs(awful.screen.focused().tags) do
                if t == awful.screen.focused().selected_tag then
                    awful.tag.seticon(icon_dir .. t.name .. "-active.png", t)
                    goto continue
                end
                for _ in pairs(t:clients()) do
                    awful.tag.seticon(icon_dir .. t.name .. "-busy.png", t)
                    goto continue
                end
                awful.tag.seticon(icon_dir .. t.name .. "-inactive.png", t)
                ::continue::
            end
        end
        update_tag_icons()

        tag.connect_signal("property::selected", function(t)
            update_tag_icons()
        end)
        tag.connect_signal("tagged", function(c)
            update_tag_icons()
        end)

        local top_panel = require("components.lines.top-panel")
        top_panel.create(s)

        local dashboard = require("components.lines.dashboard")
        dashboard.create()
    end)
end

return o
