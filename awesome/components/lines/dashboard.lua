local wibox = require("wibox")
local gears = require("gears")
local awful = require("awful")
local beautiful = require("beautiful")
local naughty = require("naughty")
local applist = require("widgets.applist")
local slider = require("widgets.lines.slider")
local brightness_slider = require("widgets.lines.brightness-slider")
local volume_slider = require("widgets.lines.volume-slider")
local button = require("widgets.lines.button")

local o = {}

function set_visibility(visible)
    screen.primary.dashboard.visible = visible
    o.applist.active = visible
end

local function create_box(w, width, height, radius)
    local box = wibox.widget {
        layout = wibox.container.margin,
        margins = radius / 2,
        {
            widget = wibox.container.background,
            forced_width = width,
            forced_height = height,
            bg = beautiful.dashboard_panel_color,
            shape = function(cr, w, h)
                return gears.shape.rounded_rect(cr, w, h, radius)
            end,
            w,
        },
    }
    return box
end

local function create_slim_button(title, callback, size)
    return {
        widget = wibox.container.margin,
        margins = size,
        wibox.widget {
            widget = button,
            update_function = function(self)
                local bg 
                if self.pressed then
                    bg = beautiful.button_active
                elseif self.hover then
                    bg = beautiful.button_hover_inactive
                else
                    bg = beautiful.button_inactive
                end
                self:get_children_by_id("background")[1].bg = bg
            end,
            on_pressed_changed = function(self, pressed)
                if pressed then
                    callback()
                end
            end,
            {
                id = "background",
                widget = wibox.widget.background,
                bg = beautiful.button_inactive,
                shape = function(cr, w, h)
                    gears.shape.rounded_bar(cr, w, h)
                end,
                {
                    layout = wibox.layout.margin,
                    margins = size,
                    {
                        widget = wibox.widget.textbox,
                        markup = title,
                        align = "center",
                        font = beautiful.menu_font or beautiful.font,
                    },
                },
            },
        },
    }
end

local function open_options_menu(title, width, height, radius, options)
    local buttons = {}
    local menu = wibox {
        ontop = true,
        type = "dock",
        visible = true,
        screen = screen.primary,
        bg = beautiful.dashboard_bg,
    }
    for _, v in ipairs(options) do
        table.insert(buttons, create_slim_button(v.text, function()
            menu.visible = false
            menu = nil
            collectgarbage("collect")
            v.callback()
        end, height / 20))
    end
    menu:setup {
        widget = wibox.widget.background,
        bg = "#00000059",
        {
            layout = wibox.layout.align.horizontal,
            expand = "none",
            nil,
            {
                layout = wibox.layout.align.vertical,
                expand = "none",
                nil,
                create_box({
                    layout = wibox.layout.align.vertical,
                    {
                        widget = wibox.container.margin,
                        top = height / 15,
                        left = height / 15,
                        right = height / 15,
                        {
                            widget = wibox.widget.textbox,
                            markup = title,
                            font = beautiful.menu_font_large or beautiful.font,
                            align = "center",
                        },
                    },
                    nil,
                    {
                        widget = wibox.container.margin,
                        margins = height / 25,
                        {
                            layout = wibox.layout.flex.horizontal,
                            table.unpack(buttons),
                        },
                    },
                },
                width,
                height,
                radius),
                nil,
            },
            nil,
        }
    }
    awful.placement.maximize(menu)
    return menu
end

local last_w, last_h

o.create = function()
    local ratio = 16 / 9
    local d_height = math.min(beautiful.dashboard_size, screen.primary.geometry.height*0.9)
    d_height = math.min(d_height, screen.primary.geometry.width/ratio * 0.9)

    local d_width = d_height * ratio

    if last_w == d_width and last_h == d_height then
        return
    end
    last_w = d_width
    last_h = d_height

    o.applist = wibox.widget {
        widget = applist,
        callback = function(self, v)
            if v == "close" then
                set_visibility(false)
            end
        end,
        height = d_height / 20,
    }
    local button_size = d_width / (4 * 3)
    local radius = button_size / 4
    left_panel = create_box(
        {
            layout = wibox.container.margin,
            margins = d_height / 15 / 2,
            {
                widget = o.applist,
            }
        }, 
        d_width / 4,
        d_height,
        radius
    )
    sliders = {}
    if settings.has_volume then
        table.insert(sliders, {
            widget = volume_slider,
            height = d_height / 20,
        })
    end
    if settings.has_brightness then
        table.insert(sliders, {
            widget = brightness_slider,
            height = d_height / 20,
        })
    end
    local center_panel = {}
    for i, v in ipairs(sliders) do
        local top = d_height / 15
        if i > 1 then
            top = d_height / 20
        end
        table.insert(center_panel,
            {
                id = "br_slider",
                widget = wibox.container.margin,
                top = top,
                left = d_height / 15,
                right = d_height / 15,
                v
            }
        )
    end
    center_panel = create_box(
        {
            layout = wibox.layout.fixed.vertical,
            table.unpack(center_panel),
        }, 
        d_width / 2,
        d_height,
        radius
    )
    local top_right_panel = create_box(
        {
            widget = wibox.widget.textbox,
            markup = "test",
        }, 
        d_width / 4,
        d_height - button_size,
        radius
    )

    local function open_poweroff_menu()
        open_options_menu("Power Off", d_width / 3, d_height / 3, radius, {
            {
                text = "Cancel",
                callback = function()
                end,
            },
            {
                text = "Suspend",
                callback = function()
                    set_visibility(false)
                    awful.spawn.with_shell("systemctl suspend")
                end,
            },
            {
                text = "Power Off",
                callback = function()
                    set_visibility(false)
                    awful.spawn.with_shell("systemctl poweroff")
                end,
            },
        })
    end

    local function open_reboot_menu()
        open_options_menu("Reboot", d_width / 3, d_height / 3, radius, {
            {
                text = "Cancel",
                callback = function()
                end,
            },
            {
                text = "Restart WM",
                callback = function()
                    awesome.restart()
                end,
            },
            {
                text = "Reboot",
                callback = function()
                    set_visibility(false)
                    awful.spawn.with_shell("systemctl reboot")
                end,
            },
        })
    end

    local function open_logout_menu()
        open_options_menu("Logout", d_width / 3, d_height / 3, radius, {
            {
                text = "Cancel",
                callback = function()
                end,
            },
            {
                text = "Lock",
                callback = function()
                    set_visibility(false)
                    awful.spawn.with_shell("dm-tool switch-to-greeter")
                end,
            },
            {
                text = "Logout",
                callback = function()
                    awesome.quit()
                end,
            },
        })
    end
    local power_button = wibox.widget {
        widget = button,
        update_function = function(self)
            local bg 
            if self.pressed then
                bg = beautiful.button_active
            elseif self.hover then
                bg = beautiful.button_hover_inactive
            else
                bg = beautiful.button_inactive
            end
            self:get_children_by_id("background")[1].bg = bg
        end,
        on_pressed_changed = function(self, pressed)
            if pressed then
                open_poweroff_menu()
            end
        end,
        {
            id = "background",
            widget = wibox.container.background,
            bg = beautiful.button_inactive,
            shape = gears.shape.circle,
            {
                widget = wibox.container.margin,
                margins = button_size / 10,
                {
                    widget = wibox.widget.imagebox,
                    image = beautiful.power_off,
                },
            },
        },
    }
    local restart_button = wibox.widget {
        widget = button,
        update_function = function(self)
            local bg 
            if self.pressed then
                bg = beautiful.button_active
            elseif self.hover then
                bg = beautiful.button_hover_inactive
            else
                bg = beautiful.button_inactive
            end
            self:get_children_by_id("background")[1].bg = bg
        end,
        on_pressed_changed = function(self, pressed)
            if pressed then
                open_reboot_menu()
            end
        end,
        {
            id = "background",
            widget = wibox.container.background,
            bg = beautiful.button_inactive,
            shape = gears.shape.circle,
            {
                widget = wibox.container.margin,
                margins = button_size / 10,
                {
                    widget = wibox.widget.imagebox,
                    image = beautiful.reboot,
                },
            },
        },
    }
    local logout_button = wibox.widget {
        widget = button,
        update_function = function(self)
            local bg 
            if self.pressed then
                bg = beautiful.button_active
            elseif self.hover then
                bg = beautiful.button_hover_inactive
            else
                bg = beautiful.button_inactive
            end
            self:get_children_by_id("background")[1].bg = bg
        end,
        on_pressed_changed = function(self, pressed)
            if pressed then
                open_logout_menu()
            end
        end,
        {
            id = "background",
            widget = wibox.container.background,
            bg = beautiful.button_inactive,
            shape = gears.shape.circle,
            {
                widget = wibox.container.margin,
                margins = button_size / 10,
                {
                    widget = wibox.widget.imagebox,
                    image = beautiful.logout,
                },
            },
        },
    }
    local bottom_right_panel = create_box(
        {
            layout = wibox.layout.fixed.horizontal,
            {
                layout = wibox.container.margin,
                margins = button_size / 5,
                forced_height = button_size,
                forced_width = button_size,
                power_button,
            },
            {
                layout = wibox.container.margin,
                margins = button_size / 5,
                forced_height = button_size,
                forced_width = button_size,
                restart_button,
            },
            {
                layout = wibox.container.margin,
                margins = button_size / 5,
                forced_height = button_size,
                forced_width = button_size,
                logout_button,
            },
        },
        d_width / 4,
        button_size,
        radius
    )
    dashboard = wibox {
        ontop = true,
        type = "dock",
        visible = false,
        screen = screen.primary,
        bg = beautiful.dashboard_bg,
    }
    dashboard : setup {
        layout = wibox.layout.align.horizontal,
        expand = "none",
        nil,
        {
            layout = wibox.layout.align.vertical,
            expand = "none",
            nil,
            {
                layout = wibox.layout.align.horizontal,
                expand = "none",
                left_panel,
                center_panel,
                {
                    layout = wibox.layout.align.vertical,
                    top_right_panel,
                    bottom_right_panel,
                }
            },
            nil,
        },
        nil,
    }
    local panels = {
        left_panel,
        center_panel,
        bottom_right_panel,
        top_right_panel,
    }

    dashboard : connect_signal("button::press", function(w, x, y, button, mods)
        if button == 1 or button == 2 or button == 3 then
            -- test if mouse was underneath a panel
            local function background_clicked(hits)
                for _, h in pairs(hits) do
                    for _, panel in pairs(panels) do
                        if h.widget == panel then
                            return false
                        end
                    end
                end
                return true
            end

            local hits = w:find_widgets(x,y)

            if background_clicked(hits) then
                set_visibility(false)
            end
        end
    end)
    awful.placement.maximize(dashboard)

    awful.screen.connect_for_each_screen(function(s)
        if s == screen.primary then
            s.dashboard = dashboard
        end
    end)
end

o.show = function()
    o.create()
    set_visibility(true)
end


return o
