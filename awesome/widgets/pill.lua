local wibox = require("wibox")
local beautiful = require("beautiful")
local gears = require("gears")

local o = {}

o.create = function(w)
    local bg = wibox.widget {
        widget = wibox.container.background,
        bg = beautiful.bg_accent,
        shape = gears.shape.rounded_bar,
        w,
    }
    return bg
end

return o
