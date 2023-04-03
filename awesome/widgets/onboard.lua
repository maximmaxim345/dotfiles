local wibox = require("wibox")
local awful = require("awful")
local beautiful = require("beautiful")
local naughty = require("naughty")
local dpi = require("beautiful.xresources").apply_dpi

local o = {}

o.create = function()
    local widget = wibox.widget {
        widget = wibox.widget.imagebox,
        id = "icon",
        image = beautiful.wifi_3,
    }
    local function handle_press(w, x, y, b, m)
        awful.spawn.with_shell("dbus-send --type=method_call --dest=org.onboard.Onboard /org/onboard/Onboard/Keyboard org.onboard.Onboard.Keyboard.ToggleVisible")
    end
    widget:connect_signal("button::press", handle_press)
    return widget
end

return o
