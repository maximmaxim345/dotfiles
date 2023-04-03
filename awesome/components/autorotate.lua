local awful = require("awful")
local wibox = require("wibox")
local beautiful = require("beautiful")
local gears = require("gears")
local naughty = require("naughty")
local lgi = require("lgi")
local glib = lgi.GLib

local o = {}

function o.setup(args)
    local indev = args.indev
    local output = args.output
    local timeout_ms = args.timeout or 5000

    local current_orientation = "normal"
    local autorotate = "ask" -- "auto", "ask" or "off"
    local function rotate(orientation)
        local o, ctm
        if orientation == "right-up" then
            ctm = "0 1 0 -1 0 1 0 0 1"
            o = "right"
        elseif orientation == "left-up" then
            ctm = "0 -1 1 1 0 0 0 0 1"
            o = "left"
        elseif orientation == "bottom-up" then
            ctm = "-1 0 1 0 -1 1 0 0 1"
            o = "inverted"
        else
            ctm = "1 0 0 0 1 0 0 0 1"
            o = "normal"
        end
        awful.spawn.easy_async_with_shell("xrandr --output "..output.." --rotation "..o)
        for _, d in pairs(indev) do
            awful.spawn.easy_async_with_shell(
                "xinput set-prop '"..d.."' 'Coordinate Transformation Matrix' "..ctm
            )
        end
        current_orientation = orientation
    end
    local popup = nil
    local timeout = nil
    local asked_orientation
    local function ask_rotation(orientation)
        if current_orientation ~= orientation then
            asked_orientation = orientation

            -- cancel the old timeout
            if timeout ~= nil then
                glib.source_remove(timeout)
            end
            -- start timeout, which will automatically hide the icon
            timeout = glib.timeout_add(glib.PRIORITY_DEFAULT, timeout_ms, function()
                -- close the popup
                popup.visible = false
                popup = nil
                return false -- delete the timer
            end)
            if popup == nil then
                popup = wibox {
                    width = 100,
                    height = 100,
                    type = "dock",
                    ontop = true,
                    visible = true,
                    screen = screen.primary,
                    bg = "transparent"
                }
                popup:setup {
                    widget = wibox.widget.background,
                    bg = beautiful.autorotate_bg,
                    shape = beautiful.autorotate_shape,
                    {
                        widget = wibox.widget.imagebox,
                        image = beautiful.autorotate_icon,
                    },
                }
                popup:connect_signal("button::press", function(w, x, y, b, m)
                    if b == 1 then
                        rotate(asked_orientation)
                        popup.visible = false
                        popup = nil
                        glib.source_remove(timeout)
                    elseif b == 3 then
                        popup.visible = false
                        popup = nil
                        glib.source_remove(timeout)
                    end
                end)

                local place
                if current_orientation == "normal" then
                    place = awful.placement.bottom_left
                elseif current_orientation == "left-up" then
                    place = awful.placement.top_left
                elseif current_orientation == "right-up" then
                    place = awful.placement.bottom_right
                elseif current_orientation == "bottom-up" then
                    place = awful.placement.top_right
                end
                place(popup, {
                    honor_workarea = true,
                    margins = beautiful.autorotate_margin,
                })
            end
        else
            if popup ~= nil then
                popup.visible = false
                popup = nil
            end
            -- cancel the old timeout
            if timeout ~= nil then
                glib.source_remove(timeout)
                timeout = nil
            end
        end
    end

    -- watch iio sensors
    awful.spawn.with_line_callback("monitor-sensor", {
        stdout = function(line)
            local light = string.match(line, "Light changed: ([%d.]+).*")
            if light ~= nil then
                return
            end

            local orientation = string.match(line, "Accelerometer orientation changed: ([%a-]+)")
            if orientation ~= nil then
                if autorotate == "auto" then
                    rotate(orientation)
                elseif autorotate == "ask" then
                    ask_rotation(orientation)
                end
                return
            end
        end,
    })
end

return o
