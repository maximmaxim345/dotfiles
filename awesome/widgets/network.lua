local wibox = require("wibox")
local awful = require("awful")
local naughty = require("naughty")
local beautiful =  require("beautiful")

local g = {}
local wlan = "wlan0"

g.create = function()
    local base_widget = wibox.widget {
        layout = wibox.layout.align.horizontal,
        {
            widget = wibox.widget.imagebox,
            id = "icon",
            resize = true,
        },
        {
            widget = wibox.widget.textbox,
            id = "network",
            markup = " ",
        }
    }

    local widget = awful.widget.watch("nmcli -c no -g device,type,state,connection device", 10, function(widget, stdout)
        local text
        local devices = {}
        for line in stdout:gmatch("[^\n\r]+") do
            local a,b,c,d = line:match("(.*):(.*):(.*):(.*)")
            table.insert(devices, {device=a, type=b, state=c, connection=d})
        end
        local d = devices[1]

        text = d.connection

        if d.type == "wifi" then
            awful.spawn.easy_async("nmcli -c no -g in-use,ssid,signal d wifi list", function(stdout, stderr, reason, exit_code)
                local icon
                local devices = {}
                local in_use = nil
                for line in stdout:gmatch("[^\n\r]+") do
                    local a,b,c = line:match("(.*):(.*):(.*)")
                    local device = {in_use=a, ssid=b, signal=c}
                    table.insert(devices, device)
                    if device.in_use == "*" then
                        in_use = device
                    end
                end
                -- local in_use = devices[1]

                local signal = tonumber(in_use.signal)

                if signal >= 75 then
                    icon = beautiful.wifi_4
                elseif signal >= 50 then
                    icon = beautiful.wifi_3
                elseif signal >= 25 then
                    icon = beautiful.wifi_2
                else
                    icon = beautiful.wifi_1
                end

                widget:get_children_by_id("icon")[1]:set_image(icon)
            end)
        elseif d.type == "ethernet" then
            -- icon = nil
            widget:get_children_by_id("icon")[1]:set_image(beautiful.ethernet)
        end
        widget:get_children_by_id("network")[1]:set_markup(text)
    end, base_widget)
    return widget
end
return g
