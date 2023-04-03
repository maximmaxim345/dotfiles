local wibox = require("wibox")
local gears = require("gears")
local naughty = require("naughty")
local beautiful = require("beautiful")

local scrollview = { mt = {} }

local properties = {
    lock_x = false, -- lock scrolling in x direction
    lock_y = false, -- lock scrolling in y direction
    step_x = 40, -- horizontal scroll step
    step_y = 40, -- vertical scroll step
    scroll_x = 0, -- horizontal scroll position
    scroll_y = 0, -- vertical scroll position
    mouse_scroll = true, -- enable mouse scrolling
    max_press_movement = 10, -- maximum movement of the mouse to scroll (to avoid accidental scrolling)
}

for prop in pairs(properties) do
    scrollview["set_"..prop] = function(self, value)
        local changed = self._private[prop] ~= value
        self._private[prop] = value

        if changed then
            self:emit_signal("property::"..prop)
            self:emit_signal("widget::redraw_needed")
        end
    end

    scrollview["get_"..prop] = function(self)
        return self._private[prop] == nil
            and properties[prop]
            or self._private[prop]
    end
end

-- currently only one widget is supported
function scrollview:set_children(children)
    self._private.widget = children[1]
    self:emit_signal("widget::layout_changed")
end

function scrollview:fit(context, width, height)
    return width, height
end

-- update the custom hierarchy
function scrollview:update_hierarchy(parent_hierarchy, force)
    if self._private.last_context == nil or
        self._private.view_width == nil or
        self._private.view_height == nil then
        -- can't update hierarchy
        return
    end
    if self._private.hierarchy == nil then
        -- create a new hierarchy TODO: test both callbacks
        self._private.hierarchy = wibox.hierarchy.new(self._private.last_context, self._private.widget,
        self._private.view_width, self._private.view_height,
        function() -- redraw callback
            self:emit_signal("widget::redraw_needed")
        end,
        function() -- layout callback
            self:emit_signal("widget::layout_changed")
            self:emit_signal("widget::redraw_needed")
        end)
    end
    -- update the matrix of the hierarchy
    if (parent_hierarchy ~= nil and parent_hierarchy._matrix_to_device ~= self._private._last_matrix_to_device)
            or (self._private._last_matrix_to_device ~= nil and force) then
        local matrix_to_device
        if parent_hierarchy == nil then
            -- use the last seen matrix
            matrix_to_device = self._private._last_matrix_to_device
        else
            -- select and save the matrix
            matrix_to_device = parent_hierarchy._matrix_to_device
            self._private._last_matrix_to_device = matrix_to_device
        end
        -- synchronize with the parents hierarchy
        self._private.hierarchy._matrix =
            gears.matrix.create_translate(self._private.scroll_x, self._private.scroll_y) *
            matrix_to_device

        self._private.hierarchy._matrix_to_device = self._private.hierarchy._matrix
        -- force update in hierarchy:update()
        self._private.hierarchy._need_update = true
    elseif force then
        self._private.hierarchy._need_update = true
    end
    -- last width of the parent
    local w, h = self._private.view_width, self._private.view_height
    h = 1000000
    -- fit the widget
    w, h = wibox.widget.base.fit_widget(self, self._private.last_context, self._private.widget, w, h)
    -- save rendered size
    self._private.rendered_width = w
    self._private.rendered_height = h
    -- recalculate the hierarchy of all children
    self._private.hierarchy:update(self._private.last_context, self._private.widget,
        w, h)
    self:scroll(0,0)
end

function scrollview:layout(context, width, height)
    -- save the context and the size
    self._private.last_context = context
    self._private.view_width = width
    self._private.view_height = height

    -- and create the hierarchy if needed
    self:update_hierarchy()
end

function scrollview:draw(context, cr, width, height)
    -- only draw if a hierarchy is available
    if self._private.hierarchy then
        cr:save()
        -- translate the context to the scroll position
        cr:translate(self._private.scroll_x, self._private.scroll_y)

        -- transform the context to the device (screen)
        cr:transform(self._private.hierarchy._matrix_to_device:invert():to_cairo_matrix())

        -- draw all children
        self._private.hierarchy:draw(context, cr, width, height)

        cr:restore()
    end
end

-- see lib/wibox/drawable.lua
local function find_widgets(_drawable, result, _hierarchy, x, y)
    local m = _hierarchy:get_matrix_from_device()

    -- Is (x,y) inside of this hierarchy or any child (aka the draw extents)
    local x1, y1 = m:transform_point(x, y)

    local x2, y2, w2, h2 = _hierarchy:get_draw_extents()
    if x1 < x2 or x1 >= x2 + w2 then
        return
    end
    if y1 < y2 or y1 >= y2 + h2 then
        return
    end
    -- Is (x,y) inside of this widget?
    local width, height = _hierarchy:get_size()
    if x1 >= 0 and y1 >= 0 and x1 <= width and y1 <= height then
        -- Get the extents of this widget in the device space
        local x3, y3, w3, h3 = gears.matrix.transform_rectangle(_hierarchy:get_matrix_to_device(),
            0, 0, width, height)
        table.insert(result, {
            x = x3, y = y3, width = w3, height = h3,
            widget_width = width,
            widget_height = height,
            drawable = _drawable,
            widget = _hierarchy:get_widget(),
            hierarchy = _hierarchy
        })
    end
    for _, child in ipairs(_hierarchy:get_children()) do
        find_widgets(_drawable, result, child, x, y)
    end
end

function scrollview:find_widgets(x, y)
    local result = {}
    if self._private.hierarchy then
        find_widgets(self, result, self._private.hierarchy, x, y)
    end
    return result
end

-- connect mouse::move for a reimplementation of mouse::enter and mouse::leave
function scrollview:setup_signals(drawable)
    if self._private.mouse_move_registered == nil then
        drawable:connect_signal("mouse::move", function(_, x, y)
            self:handle_motion(x, y)
        end)
        self._private.mouse_move_registered = true
    end
end

-- see lib/wibox/drawable.lua
local function emit_difference(name, list, skip)
    local function in_table(table, val)
        for _, v in pairs(table) do
            if v.widget == val.widget then
                return true
            end
        end
        return false
    end

    for _, v in pairs(list) do
        if not in_table(skip, v) then
            v.widget:emit_signal(name,v)
        end
    end
end

-- see lib/wibox/drawable.lua
function scrollview:handle_leave()
    emit_difference("mouse::leave", self._private._widgets_under_mouse, {})
    self._private._widgets_under_mouse = {}
end

-- see lib/wibox/drawable.lua
function scrollview:handle_motion(x, y)
    -- this does not work with the new hierarchy
    -- mouse::leave will do the job
    -- if x < 0 or y < 0 or x > self._private.view_width or y > self._private.view_height then
    --     return self:handle_leave()
    -- end

    -- Build a plain list of all widgets on that point
    local widgets_list = self:find_widgets(x, y)

    -- First, "leave" all widgets that were left
    emit_difference("mouse::leave", self._private._widgets_under_mouse, widgets_list)
    -- Then enter some widgets
    emit_difference("mouse::enter", widgets_list, self._private._widgets_under_mouse)

    self._private._widgets_under_mouse = widgets_list
end

function scrollview:scroll(x, y)
    self:scroll_to(self._private.scroll_x + x, self._private.scroll_y + y)
end

function scrollview:scroll_to(x, y)
    if self._private.rendered_height < self._private.view_height then
        y = 0
    else
        if y > 0 then
            y = 0
        end
        if y < self._private.view_height - self._private.rendered_height then
            y = self._private.view_height - self._private.rendered_height
        end
    end
    if self._private.scroll_y ~= y then
        self._private.scroll_y = y
        -- the hierarchy needs to be updated, since the position of all children has changed
        self:update_hierarchy(nil, true)
        self:emit_signal("widget::redraw_needed")
    end
end

-- reimplementation of handle_button
function scrollview:handle_button(event, x, y, button, modifiers, result)
    local function emit_at(event, x, y)
        -- calculate the absolute position of the mouse
        local ax, ay = result.hierarchy:get_matrix_to_device():transform_point(x, y)
        local widgets = self:find_widgets(ax, ay)
        for _, result in pairs(widgets) do
            -- Calculate x,y relative to the widget (just using ax, ay does not work)
            local lx, ly = result.hierarchy:get_matrix_from_device():transform_point(ax, ay)

            -- emit the button event
            result.widget:emit_signal(event, lx, ly, button, modifiers, result)
        end
    end
    -- catch all needed scroll events
    if event == "button::press" then
        if not self.lock_x then
            if button == 6 then
                self:scroll(self.step_x, 0)
                return
            elseif button == 7 then
                self:scroll(-self.step_x, 0)
                return
            end
        end
        if not self.lock_y then
            if button == 4 then
                self:scroll(0, self.step_y)
                return
            elseif button == 5 then
                self:scroll(0, -self.step_y)
                return
            end
        end
        if self.mouse_scroll and button == 1 then
            local initial_scroll_x = self._private.scroll_x
            local initial_scroll_y = self._private.scroll_y
            local only_press = true
            local max_press_move = self.max_press_movement
            local icon
            if not self.lock_x then
                icon = "sb_v_double_arrow"
            elseif not self.lock_y then
                icon = "sb_h_double_arrow"
            else
                icon = "fleur"
            end
            mousegrabber.run(function(mouse)
                if mouse.buttons[1] then
                    -- coordinates of pointer relative to the widget
                    local pX, pY = result.hierarchy:get_matrix_from_device():transform_point(mouse.x, mouse.y)
                    local dx, dy = pX - x, pY - y
                    if only_press and dx > max_press_move or dx < -max_press_move or dy > max_press_move or dy < -max_press_move then
                        only_press = false
                    end
                    if not only_press then
                        self:scroll_to(initial_scroll_x + dx, initial_scroll_y + dy)
                    end
                    return true
                end
                if only_press then
                    self:scroll_to(initial_scroll_x, initial_scroll_y)
                    emit_at("button::press", x, y)
                    emit_at("button::release", x, y)
                end

                return false
            end, icon)
            return
        end
    end
    emit_at(event, x, y)
end

function scrollview.new(args)
    -- create a base widget
    local ret = wibox.widget.base.make_widget(nil, nil, {
        enable_properties = true
    })
    gears.table.crush(ret, scrollview, true)
    -- save scroll_position so accessing the metatable is not necessary
    ret._private.scroll_x = properties.scroll_x
    ret._private.scroll_y = properties.scroll_y
    ret._private._widgets_under_mouse = {}
    ret._private.rendered_width = 0
    ret._private.rendered_height = 0

    ret:connect_signal("button::press", function(self, x, y, button, modifiers, result)
        self:update_hierarchy(result.hierarchy)
        self:setup_signals(result.drawable)
        self:handle_button("button::press", x, y, button, modifiers, result)
    end)
    ret:connect_signal("button::release", function(self, x, y, button, modifiers, result)
        self:update_hierarchy(result.hierarchy)
        self:setup_signals(result.drawable)
        self:handle_button("button::release", x, y, button, modifiers, result)
    end)
    ret:connect_signal("mouse::enter", function(self, result)
        self:update_hierarchy(result.hierarchy)
        self:setup_signals(result.drawable)
    end)
    ret:connect_signal("mouse::leave", function(self, result)
        self:update_hierarchy(result.hierarchy)
        self:setup_signals(result.drawable)
        self:handle_leave()
    end)

    return ret
end


function scrollview.mt:__call(...)
    return scrollview.new(...)
end

return setmetatable(scrollview, scrollview.mt)
