local slider = require("widgets.lines.slider")
local gears = require("gears")
local awful = require("awful")
local wibox = require("wibox")
local beautiful = require("beautiful")

local volume_slider = { mt = {} }

local properties = {
    icon = false, -- or beautiful.volume_slider_icon
    icon_muted = false, -- or beautiful.volume_slider_muted_icon
    fg = false, -- or beautiful.slider_fg
    fg_muted = false, -- or beautiful.slider_fg_inactive
    muted = false, -- real value (dont change)
    value_muted = false, -- displayed value of the slider
}

for prop in pairs(properties) do
    volume_slider["set_"..prop] = function(self, value)
        local changed = self._private[prop] ~= prop
        self._private[prop] = value

        if changed then
            self:emit_signal("property::"..prop)
            self:emit_signal("widget::redraw_needed")
        end
    end

    volume_slider["get_"..prop] = function(self)
        return self._private[prop] == nil
            and properties[prop]
            or self._private[prop]
    end
end

function volume_slider:update_style()
    local icon = self._private.icon or beautiful.volume_slider_icon
    local icon_muted = self._private.icon_muted or beautiful.volume_slider_muted_icon or icon
    local fg_normal = self._private.fg_normal or beautiful.slider_fg
    local fg_muted = self._private.fg_muted or beautiful.slider_fg_inactive or fg_normal

    local i
    if self.value == 0 or self.value_muted then
        i = icon_muted
        self._private.fg = fg_muted
    else
        i = icon
        self._private.fg = fg_normal
    end
    if self._private.leading.image ~= i then
        self._private.leading.image = i
    end
end
function volume_slider:set_fg(fg)
    local changed = self._private.fg_normal ~= fg
    self._private.fg_normal = fg

    if changed then
        self:update_style()
        self:emit_signal("property::fg")
        self:emit_signal("widget::redraw_needed")
    end
end
function volume_slider:set_fg_muted(fg_muted)
    local changed = self._private.fg_muted ~= fg_muted
    self._private.fg_muted = fg_muted

    if changed then
        self:update_style()
        self:emit_signal("property::fg_muted")
        self:emit_signal("widget::redraw_needed")
    end
end
function volume_slider:get_fg()
    return self._private.fg_normal == nil
        and properties.fg
        or self._private.fg_normal
end
function volume_slider:set_icon(icon)
    local changed = self._private.icon ~= icon
    self._private.icon = icon
    self:update_style()

    if changed then
        self:emit_signal("property::icon")
        self:emit_signal("widget::redraw_needed")
    end
end

function volume_slider:set_icon_muted(icon)
    local changed = self._private.icon_muted ~= icon
    self._private.icon_muted = icon
    self:update_style()

    if changed then
        self:emit_signal("property::icon_muted")
        self:emit_signal("widget::redraw_needed")
    end
end

function volume_slider:parse_volume(stdout)
    if self._private.v_running then
        return
    end
    local v = tonumber(stdout)
    local muted, volume = stdout:match("(.*) (.*)")

    volume = tonumber(volume)
    if muted == "true"
    then muted = true
    else muted = false end

    local v_changed = self._private.volume ~= volume
    local m_changed = self._private.muted ~= muted
    self._private.volume = volume

    self._private.muted = muted

    if v_changed then
        self:set_value(volume, true)
    end
    if m_changed then
        self:set_value_muted(muted, true)
    end
end

function volume_slider:update_volume(value)
    awful.spawn.easy_async("pamixer --set-volume "..value, function()
        self._private.volume = math.ceil(value)
        if type(self._private.v_changed) == "nil" then
            self._private.v_running = false
        else
            self:update_volume(self._private.v_changed)
            self._private.v_changed = nil
        end
    end)
end
function volume_slider:update_muted(value)
    local cmd = "pamixer "
    if value then
        cmd = cmd.."--mute"
    else
        cmd = cmd.."--unmute"
    end
    awful.spawn.easy_async_with_shell(cmd, function()
        if cmd == "true" then cmd = true
        else cmd = false end
        self._private.muted = cmd
        if type(self._private.m_changed) == "nil" then
            self._private.m_running = false
        else
            self:update_muted(self._private.m_changed)
            self._private.m_changed = nil
        end
    end)
end
function volume_slider:set_value_muted(value_muted, only_visual)
    local changed = self._private.value_muted ~= value_muted
    self._private.value_muted = value_muted

    if changed then
        self:update_style()
        self:emit_signal("property::value_muted")
        self:emit_signal("widget::redraw_needed")
    end
    if only_visual == true then
        return
    elseif self._private.m_running then
        self._private.m_changed = value_muted
    else
        self._private.m_running = true
        self:update_muted(value_muted)
    end
end
function volume_slider:set_value(value, only_visual)
    value = math.min(math.max(value, self.minimum), self.maximum)
    local changed = self._private.value ~= value
    self._private.value = value
    self._private.trailing.markup = self._private.value.."%"
    if changed then
        self:update_style()
        self:emit_signal("property::value")
        self:emit_signal("widget::redraw_needed")
    end
    if only_visual == true then
        return
    elseif self._private.v_running then
        self._private.v_changed = value
    else
        self._private.v_running = true
        self:update_volume(value)
    end
end

function volume_slider.new(args)
    local ret = wibox.widget {
        widget = slider,
        minimum = 0,
        maximum = 100,
    }
    gears.table.crush(ret, volume_slider, true)
    ret._private.v_changed = nil
    ret._private.m_changed = nil
    ret._private.v_running = false
    ret._private.m_running = false
    ret:connect_signal("leading::press", function(w, x, y, b, m)
        if b == 1 or b == 3 then
            if w.value_muted then
                w.value_muted = false
            else
                w.value_muted = true
            end
        end
    end)

    awful.widget.watch("pamixer --get-mute --get-volume", 3, ret.parse_volume, ret)

    return ret
end

function volume_slider.mt:__call(...)
    return volume_slider.new(...)
end

return setmetatable(volume_slider, volume_slider.mt)
