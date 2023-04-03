local wibox = require("wibox")
local gears = require("gears")
local awful = require("awful")
local beautiful = require("beautiful")
local dpi = require("beautiful.xresources").apply_dpi
local dashboard = require("components.lines.dashboard")

local o = {}

o.create = function(s)
    local margins = beautiful.bar_size / 10
    local pill_margins = (beautiful.bar_size - margins * 2) / 2
    -- colorful tag bar
    local tag_bar = require("widgets.lines.tag-bar").create(s)
    tag_bar = wibox.widget {
        widget = wibox.container.margin,
        margins = margins,
        tag_bar,
    }

    local battery_widget, network_widget, onboard_widget
    if settings.has_battery then
        battery_widget = require("widgets.battery").create()
    end
    if settings.draw_network_widget then
        network_widget = require("widgets.network").create()
    end
    if settings.has_touchscreen then
        onboard_widget = require("widgets.onboard").create()
    end

    local system_info = require("widgets.pill").create {
        layout = wibox.layout.margin,
        left = pill_margins,
        right = pill_margins,
        {
            layout = wibox.layout.align.horizontal,
            {
                layout = wibox.layout.margin,
                right = pill_margins,
                wibox.widget.systray(),
            },
            network_widget,
            battery_widget,
        },
    }

    local info_bar = wibox.widget {
        widget = wibox.container.margin,
        margins = margins,
        {
            layout = wibox.layout.align.horizontal,
            system_info,
        },
    }

    local panel = awful.wibar{
        position = "top",
        screen = s,
        border_width = 0,
        type = "dock",
        height = beautiful.bar_size,
        bg = beautiful.bg_normal
    }

    local clock = wibox.widget {
        widget = wibox.widget.textclock,
        format = "%I:%M %P",
    }
    local layoutbox = awful.widget.layoutbox()
    layoutbox:buttons(gears.table.join(
            awful.button({}, 1, function() awful.layout.inc(1) end),
            awful.button({}, 3, function() awful.layout.inc(-1) end),
            awful.button({}, 4, function() awful.layout.inc(1) end),
            awful.button({}, 5, function() awful.layout.inc(-1) end)))
    panel : setup {
        layout = wibox.layout.align.horizontal,
        expand = "none",
        {
            layout = wibox.layout.fixed.horizontal,
            {
                widget = wibox.container.background,
                {
                    widget = wibox.widget.imagebox,
                    image = beautiful.start_menu_icon,
                    resize = true,
                },
                buttons = gears.table.join(
                    awful.button({}, 1, function(c)
                        dashboard.show()
                    end)
                ),
            },
            tag_bar,
        },
        clock,
        {
            layout = wibox.layout.align.horizontal,
            info_bar,
            layoutbox,
            onboard_widget,
        },
    }
end

return o
