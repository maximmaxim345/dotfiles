local gears = require("gears")
local awful = require("awful")
local wibox = require("wibox")
local beautiful = require("beautiful")
local dpi = require("beautiful.xresources").apply_dpi
local pill = require("widgets.pill")

local config_dir = gears.filesystem.get_configuration_dir()
local icon_dir = config_dir .. "/icons/lines/"

local o = {}

o.create_client_option = function(args)
    local client = args.client
    local width = args.width
    local height = args.height

    -- limit the height of the bar
    local tag_bar_width = height * #client.screen.tags
    if tag_bar_width > width then
        height = width / #client.screen.tags
    end
    
    local tag_bar
    local tags_icons = {}
    local function update_icons()
        local client_tags = client:tags()
        for i, t in ipairs(client.screen.tags) do
            local state = "inactive"
            if t == client.screen.selected_tag then
                state = "active"
            elseif gears.table.hasitem(client_tags, t) then
                state = "busy"
            end
            local icon = icon_dir .. t.name .. "-" .. state .. ".png"
            tags_icons[i].image = icon
        end
    end
    for _, t in ipairs(client.screen.tags) do
        local w = wibox.widget {
            widget = wibox.widget.imagebox,
            image = icon_dir .. "1-busy.png",
            forced_width = height,
            forced_height = height,
        }
        w:connect_signal("button::press", function()
            if client.single_tag then
                client:move_to_tag(t)
            else
                client:toggle_tag(t)
                update_icons()
            end
        end)
        table.insert(tags_icons, w)
    end

    tag_bar = wibox.widget {
        layout = wibox.layout.fixed.horizontal,
        forced_height = height,
        id = "test",
        table.unpack(tags_icons),
    }
    update_icons()
    return pill.create(tag_bar)
end

o.create = function(s)
    local buttons = gears.table.join(
        awful.button(
            {}, 1, 
            function(t)
                t:view_only()
            end
        ),
        awful.button(
            {modkey}, 1, 
            function(t)
                if client.focus then
                    client.focus:move_to_tag(t)
                end
            end
        ),
        awful.button(
            {}, 3, awful.tag.viewtoggle
        ),
        awful.button(
            {modkey}, 3, 
            function(t)
                if client.focus then
                    client.focus:toggle_tag(t)
                end
            end
        ),
        awful.button({}, 4, function(t)
            awful.tag.viewnext(t.screen)
        end),
        awful.button({}, 5, function(t)
            awful.tag.viewprev(t.screen)
        end)
    )
    local tag_bar = awful.widget.taglist {
        buttons = buttons,
        screen = s,
        filter = awful.widget.taglist.filter.all,
        widget_template = {
            widget = wibox.widget.imagebox,
            id = "icon_role",
        }
    }
    tag_bar = pill.create(tag_bar)
    return tag_bar
end

return o
