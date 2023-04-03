local gears = require("gears")
local beautiful = require("beautiful")
local awful = require("awful")
local wibox = require("wibox")
local naughty = require("naughty")
local pill = require("widgets.pill")
local tagbar = require("widgets.lines.tag-bar")

-------------------------------------------------------------------------------
-- Widget for the titlebar
-------------------------------------------------------------------------------
local titlebar = { mt = {} }

function titlebar:fit(context, width, height)
    return width, self.height
end
function titlebar:draw(context, cr, width, height)
    local bg = gears.color(beautiful.titlebar_bg_focus)
    local border_size = self._private.border_size
    local size = self._private.size
    local top_size = self._private.top_size

    if self._private.position == "top" then
        local w = width - (border_size - size) * 2
        local h = top_size
        local radius = math.floor(height / 2)

        -- Draw the background
        cr:translate(border_size - size, height - top_size)

        cr:move_to(0, h)
        cr:line_to(w, h)
        cr:line_to(w, h - radius)
        cr:arc_negative(w - radius, radius, radius, 0, math.pi * 1.5)
        cr:line_to(radius, 0)
        cr:arc_negative(radius, radius, radius, math.pi * 1.5, math.pi * 1)
        cr:close_path()

        cr:set_source(bg)
        cr:fill()

        -- Draw menubuttons
        local menubutton_margin = self._private.menubutton_margin
        local bar_width = self._private.bar_width
        if bar_width > 0 then
            local bar_height = h - menubutton_margin * 2
            cr:translate(w - bar_width - menubutton_margin, h / 2 - bar_height / 2)
            gears.shape.rounded_bar(cr, bar_width, bar_height)

            cr:set_source(gears.color(beautiful.bg_accent))
            cr:fill()
        end
    elseif self._private.position == "bottom" then
        cr:move_to(width - height + size, 0)
        cr:arc(width - height, 0, size, math.pi * 1, math.pi * 0.5)
        cr:arc(width - height, 0, size, math.pi * 1, math.pi * 0.5)
        cr:line_to(height, size)
        cr:arc(height, 0, size, math.pi * 0.5, math.pi * 1)
        cr:close_path()

        cr:set_source(bg)
        cr:fill()
    elseif self._private.position == "left" then
        cr:rectangle(width - size, 0, size, height)

        cr:set_source(bg)
        cr:fill()
    elseif self._private.position == "right" then
        cr:rectangle(0, 0, size, height)
        
        cr:set_source(bg)
        cr:fill()
    end
end
function titlebar:layout(context, width, height)
    local result = {}

    if self._private.position == "top" and self._private.title ~= nil then
        -- calculate the total width needed by all children
        local size = 0
        for _, v in ipairs(self._private.widgets) do
            local w, h = wibox.widget.base.fit_widget(self, context, v, width, height)
            size = size + w
        end
        self._private.bar_width = size

        local bar_begin_x = width - self._private.border_size + self._private.size - size - self._private.menubutton_margin
        -- bar_begin_x is the leftmost position for the first child
        local x = bar_begin_x
        for _, v in ipairs(self._private.widgets) do
            -- draw the child
            local w, h = wibox.widget.base.fit_widget(self, context, v, width, height)
            table.insert(result, wibox.widget.base.place_widget_at(
                v,
                x, height / 2 - h / 2, w, h
            ))
            -- and update x for the next child
            x = x + w
        end

        -- ask how much space the title needs
        local w, h = wibox.widget.base.fit_widget(self, context, self._private.title, width, height)

        local x = width / 2 - w / 2
        local y = height / 2 - h / 2

        -- we need to test if the title is outside the titlebar or above the menubuttons
        local min_x = self._private.border_size - self._private.size
        local max_x = bar_begin_x
        -- first move the title to the left if it's too far to the right
        if x + w > max_x then
            x = max_x - w
        end
        -- then clamp it to the left
        if x < min_x then
            w = w - (min_x - x)
            x = min_x
        end

        table.insert(result, wibox.widget.base.place_widget_at(
            self._private.title,
            x, y, w, h
        ))
    end

    return result
end
-- create a new titlebar
-- a titlebar should be created for each side of each client, this will allow a more mouse friendly resize
-- expericence and a better looking border
function titlebar.create(args)
    local args = args or {}
    local position = args.position or "top" -- top, bottom, left, right
    local client = args.client -- the client to create the titlebar for
    local size = args.size or 0 -- the visible size of the titlebar
    local top_size = args.top_size or 0 -- the size of the top titlebar
    local menubutton_margin = args.menubutton_margin or 0 -- the margin between the menubuttons and the end of the titlebar
    local border_size = args.border_size or 0 -- the total size with the mouse target
    local children = args.children or {} -- all children, which will be displayed as button on top

    local ret = wibox.widget.base.make_widget(nil, nil, {
        enable_properties = true
    })
    gears.table.crush(ret, titlebar, true)

    ret._private.position = position
    ret._private.client = client
    ret._private.size = size
    ret._private.top_size = top_size
    ret._private.border_size = border_size
    ret._private.children = children
    ret._private.menubutton_margin = menubutton_margin

    if position == "top" then
        -- create the top title text
        local title = client.name ~= nil and client.name or ""
        ret._private.title = wibox.widget {
            widget = wibox.widget.textbox,
            text = title,
        }
        client:connect_signal("property::name", function()
            ret._private.title.text = client.name
        end)

        -- add menubuttons
        ret._private.widgets = children
    end

    -- attatch the button handler
    ret:connect_signal("button::press", function(w, x, y, button, mods, res)
        local function resize()
            w._private.client:emit_signal("request::activate", "titlebar", {raise = true})
            awful.mouse.client.resize(w._private.client)
        end
        local function move()
            w._private.client:emit_signal("request::activate", "titlebar", {raise = true})
            awful.mouse.client.move(w._private.client)
        end
        if w._private.position == "top" then
            -- the mouse is inside the titlebar
            if x > w._private.border_size - w._private.size and x < res.width - (w._private.border_size - w._private.size) then
                if x < res.width - w._private.bar_width - (w._private.border_size - w._private.size) then
                    -- the mouse is not above the menubuttons
                    if button == 1 then
                        move()
                    elseif button == 3 then
                        resize() -- just resize with the right mouse button
                    end
                end
                -- do nothing, if the mouse is above the menubuttons
            else
                resize()
            end
        else
            -- just resize on all other sides
            if button == 1 or button == 3 then
                resize()
            end
        end
    end)
    return ret
end
-------------------------------------------------------------------------------

-- create a generic menubutton with a margin, for a larger mouse target
local function create_menubutton(c, margins, cb, image, signals)
    local icon = wibox.widget {
        widget = wibox.widget.imagebox,
        image = image(false)
    }
    local ret = wibox.widget {
        widget = wibox.container.margin,
        -- top = margins,
        -- bottom = margins,
        margins = margins,
        icon,
    }
    ret:connect_signal("button::press", function(w, x, y, button, mods, res)
        if button == 1 then
            cb()
        end
    end)
    c:connect_signal("focus", function()
        icon.image = image(true)
    end)
    c:connect_signal("unfocus", function()
        icon.image = image(false)
    end)
    if signals then
        for _, s in ipairs(signals) do
            c:connect_signal(s, function()
                icon.image = image(true)
            end)
        end
    end
    return ret
end

-- create a close button
local function create_closebutton(c, margins)
    return create_menubutton(
        c,
        margins,
        function()
            c:kill()
        end,
        function(f)
            if f then
                return beautiful.titlebar_close_button_focus
            else
                return beautiful.titlebar_close_button_normal
            end
        end
    )
end

-- create a maximize button
local function create_maximizebutton(c, margins)
    return create_menubutton(
        c,
        margins,
        function()
            c.maximized = not c.maximized
        end,
        function(f)
            if f then
                if c.maximized then
                    return beautiful.titlebar_maximized_button_focus_active
                else
                    return beautiful.titlebar_maximized_button_focus_inactive
                end
            else
                if c.maximized then
                    return beautiful.titlebar_maximized_button_normal_active
                else
                    return beautiful.titlebar_maximized_button_normal_inactive
                end
            end
        end,
        { "property::maximized" }
    )
end

-- create a floating button
local function create_floatingbutton(c, margins)
    return create_menubutton(
        c,
        margins,
        function()
            c.floating = not c.floating
        end,
        function(f)
            if f then
                if c.floating then
                    return beautiful.titlebar_floating_button_focus_active
                else
                    return beautiful.titlebar_floating_button_focus_inactive
                end
            else
                if c.floating then
                    return beautiful.titlebar_floating_button_normal_active
                else
                    return beautiful.titlebar_floating_button_normal_inactive
                end
            end
        end,
        { "property::floating" }
    )
end

-- create a sticky button
local function create_stickybutton(c, margins)
    return create_menubutton(
        c,
        margins,
        function()
            c.sticky = not c.sticky
        end,
        function(f)
            if f then
                if c.sticky then
                    return beautiful.titlebar_sticky_button_focus_active
                else
                    return beautiful.titlebar_sticky_button_focus_inactive
                end
            else
                if c.sticky then
                    return beautiful.titlebar_sticky_button_normal_active
                else
                    return beautiful.titlebar_sticky_button_normal_inactive
                end
            end
        end,
        { "property::sticky" }
    )
end

-- create a ontop button
local function create_ontopbutton(c, margins)
    return create_menubutton(
        c,
        margins,
        function()
            c.ontop = not c.ontop
        end,
        function(f)
            if f then
                if c.ontop then
                    return beautiful.titlebar_ontop_button_focus_active
                else
                    return beautiful.titlebar_ontop_button_focus_inactive
                end
            else
                if c.ontop then
                    return beautiful.titlebar_ontop_button_normal_active
                else
                    return beautiful.titlebar_ontop_button_normal_inactive
                end
            end
        end,
        { "property::ontop" }
    )
end

-- create a button, which opens the client settings
local function create_optionsbutton(c, margins, args)
    args = args or {}
    local side_border_size = args.side_border_size or 0 -- total size of the side border
    local top_border_size = args.top_border_size or 0 -- total size of the top border
    local tagbar_height = args.tagbar_height or 0 -- height of the tagbar
    local radius = args.radius or 0 -- radius of the popup corner
    local popup_margins = args.popup_margins or 0 -- margins of the popup
    local tagbar_height = args.tagbar_height or 0 -- height of the tagbar
    local option_height = args.option_height or 0 -- height of the options

    local menu -- the open menu widget (nil if closed)
    local function close_menu()
        if menu ~= nil then
            menu.visible = false
            menu = nil
        end
    end
    local detatch_handlers
    local function press_handler(c, x, y, button, mods)
        close_menu()
        detatch_handlers()
    end
    local function unfocus_handler()
        close_menu()
        detatch_handlers()
    end
    local function position_popup()
        -- place the menu inside the client
        menu.x = c.x + c.width - menu.width - side_border_size
        menu.y = c.y + top_border_size
    end
    local function attatch_handlers()
        -- automatically close the menue if the client is pressed or unfocused
        c:connect_signal("button::press", press_handler)
        c:connect_signal("unfocus", unfocus_handler)
        c:connect_signal("property::x", position_popup)
        c:connect_signal("property::width", position_popup)
    end
    function detatch_handlers()
        c:disconnect_signal("button::press", press_handler)
        c:disconnect_signal("unfocus", unfocus_handler)
        c:disconnect_signal("property::x", position_popup)
        c:disconnect_signal("property::width", position_popup)
    end
    local function create_option(args)
        args = args or {}
        local title = args.title or "" -- title of the option
        local height = args.height or 50 -- height of the widget
        local initial_state = args.state or false -- initial state of the widget
        -- callback function (parameter is the old state, returns the new state)
        local callback = args.callback or function(prev) return not prev end

        local checkbox_height = height / 2
        local checkbox = wibox.widget {
            widget = wibox.widget.checkbox,
            color = beautiful.bg_accent,
            paddings = checkbox_height / 4,
            border_width = checkbox_height / 10,
            shape = gears.shape.circle,
            checked = initial_state,
        }
        checkbox:connect_signal("button::press", function()
            checkbox.checked = callback(checkbox.checked)
        end)
        return wibox.widget {
            layout = wibox.layout.fixed.horizontal,
            forced_height = height,
            {
                layout = wibox.layout.margin,
                margins = (height - checkbox_height) / 2,
                checkbox,
            },
            {
                widget = wibox.widget.textbox,
                markup = title,
            }
        }
    end
    local function open_menu()
        -- open new options menu for the client
        close_menu()
        local tagbar_width = tagbar_height * #c.screen.tags
        menu = wibox {
            ontop = true,
            type = "menu", -- or "dock"
            bg = "transparent",
            border_width = 0,
            height = tagbar_height + 4 * option_height + popup_margins * 2,
            width = tagbar_width + popup_margins * 2,
        }
        menu:setup{
            widget = wibox.widget.background,
            bg = beautiful.titlebar_bg_focus,
            shape = function(cr, w, h)
                gears.shape.partially_rounded_rect(cr, w, h, false, false, false, true, radius)
            end,
            {
                layout = wibox.layout.margin,
                margins = popup_margins,
                {
                    widget = wibox.layout.fixed.vertical,
                    create_option {
                        title = "ontop",
                        height = option_height,
                        state = c.ontop,
                        callback = function(prev)
                            c.ontop = not c.ontop
                            return c.ontop
                        end,
                    },
                    create_option {
                        title = "sticky",
                        height = option_height,
                        state = c.sticky,
                        callback = function(prev)
                            c.sticky = not c.sticky
                            return c.sticky
                        end,
                    },
                    create_option {
                        title = "floating",
                        height = option_height,
                        state = c.floating,
                        callback = function(prev)
                            c.floating = not c.floating
                            return c.floating
                        end,
                    },
                    create_option {
                        title = "single tag",
                        height = option_height,
                        state = c.single_tag or false,
                        callback = function(prev)
                            c.single_tag = not c.single_tag
                            return c.single_tag
                        end,
                    },
                    tagbar.create_client_option{
                        client = c,
                        height = tagbar_height,
                        width = tagbar_width,
                    },
                },
            },
        }
        position_popup()

        -- show the menu
        menu.visible = true
        attatch_handlers()
    end

    -- return the button widget
    return create_menubutton(
        c,
        margins,
        function()
            open_menu()
        end,
        function(f)
            if f then
                return beautiful.titlebar_ontop_button_focus_inactive
            else
                return beautiful.titlebar_ontop_button_normal_inactive
            end
        end
    )
end

-- attatch the titlebar to the client
client.connect_signal("request::titlebars", function(c)
    local margin = beautiful.bar_size / 10
    local border_size = beautiful.interactive_border_width or 0
    local visible_border_size = 4
    local top_size = beautiful.bar_size

    local top_border = awful.titlebar(c, {
        size = top_size,
        position = "top",
        bg_normal = "transparent", bg_focus = "transparent", bg_urgent = "transparent",
    })
    
    -- add top border
    top_border:setup{
        layout = wibox.layout.stack, -- we can't directly place a widget here
        titlebar.create {
            position = "top",
            client = c,
            border_size = border_size,
            size = visible_border_size,
            top_size = top_size,
            menubutton_margin = margin,
            children = {
                create_optionsbutton(c, margin, {
                    side_border_size = border_size,
                    top_border_size = top_size,
                    tagbar_height = top_size - 2 * margin,
                    radius = top_size / 2,
                    popup_margins= top_size / 6,
                    option_height = top_size,
                }),
                create_maximizebutton(c, margin),
                create_closebutton(c, margin),
            }
        }
    }

    -- add side borders
    if border_size > 0 then
        local function create_side_border(position)
            local border = awful.titlebar(c, {size = border_size, position = position,
                bg_normal = "transparent", bg_focus = "transparent", bg_urgent = "transparent" })
            border:setup {
                layout = wibox.layout.stack,
                titlebar.create {
                    position = position,
                    client = c,
                    border_size = border_size,
                    size = visible_border_size,
                }
            }
            return border
        end
        create_side_border("left")
        create_side_border("right")
        create_side_border("bottom")
    end
end)
