local wibox = require("wibox")
local gears = require("gears")
local naughty = require("naughty")
local beautiful = require("beautiful")
local dpi = require("beautiful.xresources").apply_dpi
local GLib = require("lgi").GLib

local slider = { mt = {} }

local properties = {
    value = 0,
    minimum = 0,
    maximum = 100,
    height = 40,
    scroll_step = 5,
    interactive = true,
    fg = false, -- or beautiful.slider_fg
    bg = false, -- or beautiful.slider_bg
}
-- events:
-- leading::press - icon pressed
-- trailing::press - text pressed

for prop in pairs(properties) do
    slider["set_"..prop] = function(self, value)
        local changed = self._private[prop] ~= value
        self._private[prop] = value

        if changed then
            self:emit_signal("property::"..prop)
            self:emit_signal("widget::redraw_needed")
        end
    end

    slider["get_"..prop] = function(self)
        return self._private[prop] == nil
            and properties[prop]
            or self._private[prop]
    end
end
function slider:set_height(height)
    local changed = self._private.height ~= height
    self._private.height = height

    if changed then
        self:emit_signal("property::height")
        self:emit_signal("widget::redraw_needed")
    end
end

function slider:set_icon(icon)
    local changed = self._private.icon ~= icon
    self._private.icon = icon
    self._private.leading.image = icon

    if changed then
        self:emit_signal("property::icon")
        self:emit_signal("widget::redraw_needed")
    end
end

function slider:set_value(value)
    local changed = self._private.value ~= value
    self._private.value = math.min(math.max(value, self.minimum), self.maximum)
    self._private.trailing.markup = self._private.value.."%"

    if changed then
        self:emit_signal("property::value")
        self:emit_signal("widget::redraw_needed")
    end
end

function slider:draw(context, cr, width, height)
    height = self.height

    local bg = gears.color(self._private.bg or beautiful.slider_bg or "#aaaaaa")
    local fg = gears.color(self._private.fg or beautiful.slider_fg or "#ffffff")

    local range = self.maximum - self.minimum

    local bar_width = width * 0.75
    local bar_offset = (width - bar_width) / 2
    local bar_width_active = (bar_width - height) * ((self.value - self.minimum) / range) + height

    cr:save()
    cr:translate(bar_offset, 0)
    -- draw background of bar
    gears.shape.rounded_bar(cr, bar_width, height)
    cr:set_source(bg)
    cr:fill()

    -- draw bar
    gears.shape.rounded_bar(cr, bar_width_active, height)
    cr:set_source(fg)
    cr:fill()

    cr:restore()

    -- draw icon

    cr:save()
    cr:set_source(gears.color("#ffffff"))
    self._private.leading:draw(context, cr, (width - bar_width) / 2, height)
    cr:restore()

    -- draw value

    cr:set_source(gears.color("#ffffff"))
    cr:translate(width - (width - bar_width) / 2, 0)
    self._private.trailing:draw(context, cr, (width - bar_width) / 2, height)
end

function slider:fit(context, width, height)
    return width, self.height
end

local function coordinates_to_value(self, x, widget_width)
    local padding = self.height / 2
    local margin = widget_width * 0.25 * 0.5

    local range = self.maximum - self.minimum
    -- offset to center of circle
    local width = widget_width - (padding + margin) * 2

    local value = math.floor(
        ((x - padding - margin) * range)
        / width + self.minimum
    )
    local outside = (x < margin) or (x > widget_width - margin)
    return value, outside
end

local function button_press(self, x, y, button, mod, result)
    local value, outside = coordinates_to_value(self, x, result.widget_width)
    if outside then
        if value < self.minimum then
            self:emit_signal("leading::press", x, y, button, mod, result)
        else
            self:emit_signal("trailing::press", x, y, button, mod, result)
        end
        return
    end
    if not self.interactive then
        return
    end

    if button == 4 then
        self.value = self.value + self.scroll_step
    elseif button == 5 then
        self.value = self.value - self.scroll_step
    elseif button == 1 or button == 3 then
        self.value = value
        -- naughty.notify({
        --     text = "x "..tostring(result.x).." y "..tostring(result.y),
        -- })

        mousegrabber.run(function(mouse)
            if mouse.buttons[1] or mouse.buttons[2] or mouse.buttons[3] then
                -- coordinates of pointer relative to the widget
                local pX, pY = result.hierarchy:get_matrix_from_device():transform_point(mouse.x, mouse.y)

                self.value = coordinates_to_value(self, pX, result.widget_width)

                return true
            end

            return false
        end, "sb_h_double_arrow")
    end
end

function slider.new(args)
    local ret = wibox.widget.base.make_widget(nil, nil, {
        enable_properties = true
    })
    gears.table.crush(ret, slider, true)

    ret._private.leading = wibox.widget {
        widget = wibox.widget.imagebox,
        resize = true,
        icon = nil,
    }
    ret._private.trailing = wibox.widget {
        widget = wibox.widget.textbox,
        markup = properties.value.."%",
        font = beautiful.slider_font or beautiful.font,
        align = "center",
    }

    ret:connect_signal("button::press", button_press)

    return ret
end


function slider.mt:__call(...)
    return slider.new(...)
end

return setmetatable(slider, slider.mt)
