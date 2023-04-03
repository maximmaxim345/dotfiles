local wibox = require("wibox")
local gears = require("gears")
local naughty = require("naughty")
local beautiful = require("beautiful")
local dpi = require("beautiful.xresources").apply_dpi
local GLib = require("lgi").GLib

local button = { mt = {} }

local properties = {
    toggle = false,
    hover = false,
    pressed = false,
    update_function = false, -- function(self)
    on_pressed_changed = false, -- function(self, pressed)
}

for prop in pairs(properties) do
    button["set_"..prop] = function(self, value)
        local changed = self._private[prop] ~= value
        self._private[prop] = value


        if changed then
            if (prop == "hover" or prop == "pressed") and type(self._private.update_function) == "function" then
                self._private.update_function(self)
            end
            if prop == "pressed" and type(self._private.on_pressed_changed) == "function" then
                self._private.on_pressed_changed(self, value)
            end
            self:emit_signal("property::"..prop)
            self:emit_signal("widget::redraw_needed")
        end
    end

    button["get_"..prop] = function(self)
        return self._private[prop] == nil
            and properties[prop]
            or self._private[prop]
    end
end

function button:layout(_, width, height)
    if self._private.widget ~= nil then
        return {wibox.widget.base.place_widget_at(self._private.widget, 0, 0, width, height) }
    end
end
function button:set_children(children)
    self._private.widget = children[1]
    self:emit_signal("widget::layout_changed")
end

function button:fit(context, width, height)
    if self._private.widget ~= nil then
        return wibox.widget.base.fit_widget(self, context, self._private.widget, width, height)
    else
        return 0, 0
    end
end

function button.new(args)
    local args = args or {}

    local ret = wibox.widget.base.make_widget(nil, nil, {
        enable_properties = true,
    })
    gears.table.crush(ret, button, true)

    ret._private.pressed = false

    ret:connect_signal("button::press", function(w, _, _, button)
        if button == 1 then
            if w.toggle then
                w.pressed = not w.pressed
            else
                w.pressed = true
            end
        end
    end)
    ret:connect_signal("button::release", function(w, _, _, button)
        if button == 1 then
            if not w.toggle then
                w.pressed = false
            end
        end
    end)
    ret:connect_signal("mouse::enter", function(w)
        w.hover = true
    end)
    ret:connect_signal("mouse::leave", function(w)
        w.hover = false
        if not w.toggle then
            w.pressed = false
        end
    end)

    return ret
end

function button.mt:__call(...)
    return button.new(...)
end

return setmetatable(button, button.mt)
