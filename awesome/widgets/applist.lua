local wibox = require("wibox")
local gears = require("gears")
local awful = require("awful")
local beautiful = require("beautiful")
local naughty = require("naughty")
local menugen = require("menubar.menu_gen")
local fzy = require("lib.fzy_lua")
local scrollview = require("widgets.scrollview")
local button = require("widgets.lines.button")

local applist = { mt = {} }

local properties = {
    height = 30,
    active = false,
    callback = false, -- function(v) end
                      -- v is "close"
}

for prop in pairs(properties) do
    applist["set_"..prop] = function(self, value)
        local changed = self._private[prop] ~= value
        self._private[prop] = value

        if changed then
            self:emit_signal("property::"..prop)
            self:emit_signal("widget::redraw_needed")
        end
    end

    applist["get_"..prop] = function(self)
        return self._private[prop] == nil
            and properties[prop]
            or self._private[prop]
    end
end

-- list of all installed apps
local software_entries = {}

function applist.update_index()
    menugen.generate(function(entries)
        -- TODO: replace with a custom function
        software_entries = entries
        -- entry = name,cmdline,icon,category
    end)
end
-- fill the list
applist.update_index()

function applist:start_software(entry)
    -- start the entry
    awful.spawn(entry.cmdline)

    -- close the widget
    if type(self._private.callback) == "function" then self._private.callback(self, "close") end
    self._private.active = false
    self:emit_signal("property::active")
end

-------------------------------------------------------------------------------
-- Widget for a list item
-------------------------------------------------------------------------------
local list_item = { mt = {} }

function list_item:set_height(height)
    local changed = self.height ~= height
    self._private.height = height

    if changed then
        self:emit_signal("property::height")
        self:emit_signal("widget::redraw_needed")
    end
end
function list_item:get_height()
    return self._private.height == nil
        and 30
        or self._private.height
end
function list_item:set_selected(selected)
    local changed = self.selected ~= selected
    self._private.selected = selected

    if changed then
        self:emit_signal("property::selected")
        self:emit_signal("widget::redraw_needed")
    end
end
function list_item:get_selected()
    return self._private.selected
end
function list_item:set_name(name)
    local changed = self._private.name ~= name
    self._private.name = name
    self._private.text.text = name

    if changed then
        self:emit_signal("property::name")
        self:emit_signal("widget::redraw_needed")
    end
end
function list_item:get_name()
    return self._private.name
end
function list_item:set_icon(icon)
    local changed = self._private.icon ~= icon
    self._private._icon = icon
    self._private.icon.image = icon

    if changed then
        self:emit_signal("property::icon")
        self:emit_signal("widget::redraw_needed")
    end
end
function list_item:get_icon()
    return self._private._icon
end
function list_item:set_selectable(selectable)
    selectable = selectable == nil and true or selectable
    local changed = self._private.selectable ~= selectable
    self._private.selectable = selectable

    if changed then
        if not selectable then
            self._private.hover = false
            self._private.pressed = false
        end
        self:emit_signal("property::selectable")
        self:emit_signal("widget::redraw_needed")
    end
end
function list_item:get_selectable()
    return self._private.selectable
end
function list_item:set_seperator(seperator)
    seperator = seperator == nil and false or seperator
    local changed = self._private.seperator ~= seperator
    self._private.seperator = seperator

    if changed then
        self:emit_signal("property::seperator")
        self:emit_signal("widget::layout_changed")
    end
end
function list_item:get_seperator()
    return self._private.seperator
end
function list_item:set_callback(callback)
    self._private.callback = callback
end
function list_item:get_callback()
    return self._private.callback
end
function list_item:fit(context, width, height)
    return width, self.height
end
function list_item:draw(context, cr, width, height)
    if self._private.seperator then
        local from = self._private.seperator_start or 0
        cr:move_to(from, height / 2)
        cr:line_to(width, height / 2)
        cr:set_source(gears.color("#ffffff40"))
        cr:stroke()
    else
        local bg
        if self._private.pressed then
            bg = gears.color(beautiful.button_active)
        elseif self._private.hover or self._private.selected then
            bg = gears.color(beautiful.button_hover_inactive)
        else
            bg = gears.color("transparent")
        end
        if self._private.seperator then
            bg = gears.color("#ffffff45")
        end
        cr:set_source(bg)
        gears.shape.rounded_bar(cr, width, height)
        cr:fill()
    end
end
function list_item:layout(context, width, height)
    local margin_lr = 5 -- left and right margin
    local margin_tb = 2 -- top and bottom margin
    local margin_icon = 5 -- margin between icon and text
    local image_size = height -- assume icon is square

    local image_pos_x = margin_lr
    local text_pos_x = image_pos_x + image_size + margin_icon
    local text_w = width - image_size - 2 * margin_lr

    if self._private.seperator then
        text_pos_x = margin_lr
        text_w = width - 2 * margin_lr
        local w, h = wibox.widget.base.fit_widget(self, context, self._private.text, text_w, height)
        text_w = w
        self._private.seperator_start = text_pos_x + text_w + margin_lr
    end

    local result = {}
    table.insert(result, wibox.widget.base.place_widget_at(self._private.text,
        text_pos_x,
        margin_tb,
        text_w,
        height - 2 * margin_tb))
    table.insert(result, wibox.widget.base.place_widget_at(self._private.icon,
        image_pos_x,
        margin_tb,
        image_size,
        image_size - 2 * margin_tb))
    return result
end
function list_item.new(args)
    local ret = wibox.widget.base.make_widget(nil, nil, {
        enable_properties = true
    })
    gears.table.crush(ret, list_item, true)
    ret._private.pressed = false
    ret._private.hover = false
    ret._private.selected = false
    ret._private.selectable = true
    ret._private.seperator = false
    ret._private.text = wibox.widget {
        widget = wibox.widget.textbox,
        font = beautiful.applist_font or beautiful.font,
    }
    ret._private.icon = wibox.widget {
        widget = wibox.widget.imagebox,
    }
    ret:connect_signal("button::press", function(self, lx, ly, button, modifiers)
        if not self._private.selectable then return end
        self._private.pressed = true
        self:emit_signal("widget::redraw_needed")
        if button == 1 then
            if type(self._private.callback) == "function" then
                self._private.callback(self, "press")
            end
        end
    end)
    ret:connect_signal("button::release", function(self, lx, ly, button, modifiers)
        if not self._private.selectable then return end
        self._private.pressed = false
        self:emit_signal("widget::redraw_needed")
    end)
    ret:connect_signal("mouse::enter", function(self)
        if not self._private.selectable then return end
        self._private.hover = true
        self:emit_signal("widget::redraw_needed")
        if type(self._private.callback) == "function" then
            self._private.callback(self, "enter")
        end
    end)
    ret:connect_signal("mouse::leave", function(self)
        if not self._private.selectable then return end
        self._private.hover = false
        self:emit_signal("widget::redraw_needed")
    end)
    return ret
end

function list_item.mt:__call(...)
    return list_item.new(...)
end
list_item = setmetatable(list_item, list_item.mt)
-------------------------------------------------------------------------------

function applist:update_results(cmd)
    -- deselect active result
    self._private.selected = 0

    local input = cmd
    local options = {}
    local results = {}
    local search = false
    local sort_by_name = false
    local filter_by_name = false
    if input == "" then
        local favorites = {
            "Brave",
            "Nemo",
            "kitty",
            "Octopi",
            "SpeedCrunch",
            "SuperSlicer",
            "KOReader",
        }

        for _, name in ipairs(favorites) do
            for _, e in pairs(software_entries) do
                if e.name == name then
                    table.insert(results, {
                        option = {
                            icon = e.icon,
                            name = e.name,
                            entry = e,
                        },
                    })
                    break
                end
            end
        end

        table.insert(results, {
            option = {
                icon = nil,
                name = "",
            },
            selectable = false,
            seperator = true,
        })

        table.insert(results, {
            option = {
                name = "All Apps",
                cmd = ":all "
            },
        })
        table.insert(results, {
            option = {
                name = "By Category",
                cmd = ":"
            },
        })
    elseif input:sub(1, 4) == ":all" then
        input = input:sub(5)
        sort_by_name = true
        for _, e in ipairs(software_entries) do
            table.insert(options, {
                icon = e.icon,
                name = e.name,
                entry = e,
            })
        end
    elseif input:sub(1, 1) == ":" then
        input = input:sub(2)
        filter_by_name = true
        options = {
            { name = "All Apps" },
            { name = "Favorites" },
            { name = "System" },
            { name = "Settings" },
            { name = "Terminal" },
            { name = "Web Browser" },
            { name = "File Manager" },
            { name = "Graphics" },
            { name = "Multimedia" },
            { name = "Development" },
            { name = "Games" },
            { name = "Office" },
            { name = "System Tools" },
            { name = "Utilities" },
            { name = "Other" },
        }
    else
        search = true
        for _, e in ipairs(software_entries) do
            table.insert(options, {
                icon = e.icon,
                name = e.name,
                entry = e,
            })
        end
    end

    if search then
        -- Search for apps
        for _, o in pairs(options) do
            local score = fzy.score(input, o.name)
            -- skip if score is 0
            if score == -math.huge then
                goto continue
            end
            -- prioritize a direct match
            local match = fzy.has_match(input, o.name)
            table.insert(results, {
                score = score,
                match = match,
                option = o,
            })
            ::continue::
        end
        -- sort by score
        table.sort(results, function(a,b)
            if b.match == a.match then
                return a.score > b.score
            else
                return a.match
            end
        end)
    elseif sort_by_name then
        -- Show all apps
        for i, o in ipairs(options) do
            table.insert(results, {
                option = o,
            })
        end
        -- sort by name
        table.sort(results, function(a,b)
            return a.option.name:upper() < b.option.name:upper()
        end)
        -- insert letter headers between apps
        last_letter = ""
        for i=1, #results do
            local letter = results[i].option.name:sub(1,1):upper()
            if letter ~= last_letter then
                table.insert(results, i, {
                    option = {
                        name = letter,
                        icon = nil,
                    },
                    selectable = false,
                    seperator = true,
                })
                last_letter = letter
            end
        end
    elseif filter_by_name then
        -- Show apps that match input
        for i, o in ipairs(options) do
            -- prioritize a direct match
            local match = fzy.has_match(input, o.name)
            if match then
                table.insert(results, {
                    option = o,
                })
            end
        end
    end
    -- update the list:
    -- number of widgets in the list before update
    local prev_widgets_num = #self._private.resultlist.children
    for i, r in pairs(results) do
        local name = r.option.name
        local icon = r.option.icon
        local selectable = r.selectable
        local seperator = r.seperator
        local callback
        if r.option.cmd ~= nil then
            callback = function(w, action)
                if action == "press" then
                    self:set_cmd(r.option.cmd)
                    return false
                elseif action == "enter" then
                    if self._private.selected > 0 then
                        self._private.resultlist.children[self._private.selected].selected = false
                        self._private.selected = 0
                    end
                end
            end
        else
            callback = function(w, action)
                if action == "press" then
                    self:start_software(r.option.entry)
                    return true
                elseif action == "enter" then
                    if self._private.selected > 0 then
                        self._private.resultlist.children[self._private.selected].selected = false
                        self._private.selected = 0
                    end
                end
            end
        end
        local selected = i == self._private.selected
        if prev_widgets_num < i then
            local w = wibox.widget {
                widget = list_item,
                height = self.height,
                name = name,
                icon = icon,
                selectable = selectable,
                seperator = seperator,
                callback = callback,
                selected = selected,
            }
            self._private.resultlist:add(w)
        else
            self._private.resultlist.children[i]:set_name(name)
            self._private.resultlist.children[i]:set_icon(icon)
            self._private.resultlist.children[i]:set_selectable(selectable)
            self._private.resultlist.children[i]:set_seperator(seperator)
            self._private.resultlist.children[i]:set_callback(callback)
            self._private.resultlist.children[i]:set_selected(selected)
        end
    end
    -- remove unused widgets
    local widgets_num = #results
    if prev_widgets_num > widgets_num then
        if widgets_num > 0 then
            for i = prev_widgets_num, widgets_num + 1, -1 do
                self._private.resultlist:remove(i)
            end
        else
            self._private.resultlist:reset()
        end
    end
end

local function remove_hover(self)
    for _, w in pairs(self._private.resultlist.children) do
        if w._private.hover == true then
            w._private.hover = false
            self:emit_signal("widget::redraw_needed")
        end
    end
end

local function show(self, cmd)
    cmd = type(cmd) == "string" and cmd or ""
    self:update_results(cmd)
    awful.prompt.run {
        text = cmd,
        font = beautiful.applist_font or beautiful.font,
        textbox = self._private.textbox,
        done_callback = function()
            if self._private.new_cmd ~= nil then
                show(self, self._private.new_cmd)
                self._private.new_cmd = nil
                return
            end
            self._private.active = false
            self:emit_signal("property::active")
        end,
        changed_callback = function(cmd)
            self:update_results(cmd)
        end,
        hooks = {
            {{}, "Up", function(cmd)
                if self._private.selected > 1 then
                    remove_hover(self)
                    self._private.resultlist.children[self._private.selected].selected = false
                    self._private.selected = self._private.selected - 1
                    self._private.resultlist.children[self._private.selected].selected = true
                end
                return nil, false
            end},
            {{}, "Down", function(cmd)
                if self._private.selected < #self._private.resultlist:get_children() then
                    remove_hover(self)
                    if self._private.selected > 0 then
                        self._private.resultlist.children[self._private.selected].selected = false
                    end
                    self._private.selected = self._private.selected + 1
                    self._private.resultlist.children[self._private.selected].selected = true
                end
                return nil, false
            end},
            {{}, "Escape", function(_)
                if self._private.new_cmd ~= nil then return nil, true end
                if type(self._private.callback) == "function" then self._private.callback(self, "close") end
            end},
            {{}, "Return", function(_)
                local exit = true
                if #self._private.resultlist.children > 0 then
                    local i
                    if self._private.selected > 0 then
                        i = self._private.selected
                    else
                        i = 1
                    end
                    local w = self._private.resultlist.children[i]
                    if type(w.callback) == "function" then
                        exit = w:callback("press")
                    else
                        exit = false
                    end
                end
                return nil, exit
            end},
        },
    }
end

local function hide(self, no_reset)
    -- simulate a keypress to close the prompt
    root.fake_input("key_press", "Escape")
    root.fake_input("key_release", "Escape")
    if no_reset ~= true then
        self._private.resultlist:reset()
    end
end

function applist:set_cmd(cmd)
    self._private.new_cmd = cmd
    hide(self, true)
end

function applist:set_active(active)
    local changed = self._private.active ~= active
    self._private.active = active

    if changed then
        if active then
            show(self)
        else
            hide(self)
        end
        self:emit_signal("property::active")
        self:emit_signal("widget::redraw_needed")
    end
end

function applist:set_height(height)
    local changed = self._private.height ~= height
    self._private.height = height

    if changed then
        self._private.widget:get_children_by_id("textboxbg")[1].forced_height = height
        self:emit_signal("property::height")
        self:emit_signal("widget::layout_changed")
        self:emit_signal("widget::redraw_needed")
    end
end

function applist:layout(context, width, height)
    return {wibox.widget.base.place_widget_at(self._private.widget, 0, 0, width, height)}
end

function applist:fit(context, width, height)
    return wibox.widget.base.fit_widget(self, context, self._private.widget, width, height)
end

-- create the widget
function applist.new(args)
    local ret = wibox.widget.base.make_widget(nil, nil, {
        enable_properties = true
    })
    gears.table.crush(ret, applist, true)

    ret._private.textbox = wibox.widget {
        widget = wibox.widget.textbox,
    }
    ret._private.resultlist = wibox.widget {
        layout = wibox.layout.fixed.vertical,
    }
    ret._private.widget = wibox.widget {
        layout = wibox.layout.fixed.vertical,
        {
            id = "textboxbg",
            widget = wibox.container.background,
            bg = "#ffffff45",
            forced_height = ret.height,
            shape = gears.shape.rounded_bar,
            {
                layout = wibox.layout.align.horizontal,
                expand = "none",
                nil,
                ret._private.textbox,
            },
        },
        {
            widget = scrollview,
            ret._private.resultlist,
        }
    }

    ret._private.selected = 0

    return ret
end

function applist.mt:__call(...)
    return applist.new(...)
end

return setmetatable(applist, applist.mt)
