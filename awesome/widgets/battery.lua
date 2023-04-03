local wibox = require("wibox")
local awful = require("awful")
local beautiful = require("beautiful")
local naughty = require("naughty")
local dpi = require("beautiful.xresources").apply_dpi

local o = {}

o.create = function()
    local function get_icon(percentage)
        if percentage >= 90 then
            return beautiful.battery_100
        elseif percentage >= 70 then
            return beautiful.battery_80
        elseif percentage >= 50 then
            return beautiful.battery_60
        elseif percentage >= 30 then
            return beautiful.battery_40
        elseif percentage >= 15 then
            return beautiful.battery_20
        else
            return beautiful.battery_0
        end
    end
    local function show_popup()
        awful.spawn.easy_async("acpi -bt", function(stdout)
            local percentage = 0
            for line in stdout:gmatch("[^\r\n]+") do
                _, percentage, _ = string.match(stdout, "Battery +%d: (%a+), (%d+)%%?,? ?(.*)")
                percentage = tonumber(percentage)
            end
            naughty.notify {
                title = "Battery status",
                hover_timeout = 0.1,
                timeout = 8,
                position = "top_right",
                screen = mouse.screen,
                icon = get_icon(percentage),
                text = stdout,
            }
        end)
    end
    local base_widget = wibox.widget {
        layout = wibox.layout.align.horizontal,
        {
            widget = wibox.widget.imagebox,
            id = "state-icon",
        },
        {
            widget = wibox.widget.imagebox,
            id = "icon",
        },
        {
            widget = wibox.widget.textbox,
            id = "text",
            markup = " ",
        },
    }
    -- Battery 0: Discharging, 41%, 02:31:36 remaining
    -- Battery 0: Unknown, 97%
    local widget = awful.widget.watch("acpi -b", 5, function(widget, stdout)
        local state, percentage, remaining

        for line in stdout:gmatch("[^\r\n]+") do
            state, percentage, remaining = string.match(stdout, ".+: (%a+), (%d+)%%?,? ?(.*)")
            percentage = tonumber(percentage)
        end

        local charging = state == "Charging"

        local text = percentage .. "%"
        local icon, state_icon

        icon = get_icon(percentage)
        
        if charging then
            state_icon = beautiful.battery_charging
        end

        widget : get_children_by_id("text")[1]:set_markup(text)
        widget : get_children_by_id("icon")[1]:set_image(icon)
        widget : get_children_by_id("state-icon")[1]:set_image(state_icon)
    end, base_widget)
    widget:connect_signal("button::press", show_popup)
    return widget
end

return o
