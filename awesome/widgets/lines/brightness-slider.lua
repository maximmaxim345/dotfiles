local slider = require("widgets.lines.slider")
local gears = require("gears")
local awful = require("awful")
local wibox = require("wibox")
local beautiful = require("beautiful")

local brightness_slider = { mt = {} }

-- only for reference
local properties = {
    icon = false, -- or beautiful.brightness_slider_icon
}

function brightness_slider:parse_brightness(stdout)
    if self._private.br_running then
        return
    end
    local br = math.ceil(tonumber(stdout))

    local changed = self._private.brightness ~= br
    self._private.brightness = br
    if changed then
        self:set_value(br, true)
    end
end

function brightness_slider:update_brightness(value)
    awful.spawn.easy_async("light -S "..value, function()
        self._private.brightness = math.ceil(value)
        if type(self._private.br_changed) == "nil" then
            self._private.br_running = false
        else
            self:update_brightness(self._private.br_changed)
            self._private.br_changed = nil
        end
    end)
end
function brightness_slider:set_value(value, only_visual)
    value = math.min(math.max(value, self.minimum), self.maximum)
    local changed = self._private.value ~= value
    self._private.value = value
    self._private.trailing.markup = self._private.value.."%"
    if changed then
        self:emit_signal("widget::redraw_needed")
    end
    if only_visual == true then
        return
    elseif self._private.br_running then
        self._private.br_changed = value
    else
        self._private.br_running = true
        self:update_brightness(value)
    end
end

function brightness_slider.new(args)
    local ret = wibox.widget {
        widget = slider,
        minimum = 1,
        maximum = 100,
    }
    gears.table.crush(ret, brightness_slider, true)
    ret._private.br_changed = nil
    ret._private.br_running = false
    ret.icon = beautiful.brightness_slider_icon

    awful.widget.watch("light -G", 10, ret.parse_brightness, ret)

    return ret
end

function brightness_slider.mt:__call(...)
    return brightness_slider.new(...)
end

return setmetatable(brightness_slider, brightness_slider.mt)
