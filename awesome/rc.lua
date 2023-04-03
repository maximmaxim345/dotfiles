local gears = require("gears")
local awful = require("awful")

-- list of themes
local themes =
{
    "lines"
}

settings = {
    has_brightness = false,
    has_volume = true,
    has_battery = false,
    has_network = true,
    has_bluetooth = false,
    has_touchscreen = false,
    use_nm_applet = true,
    apps = {
    },
    ts_rotate = { -- devices which need to be rotated
        indev = { -- from "xinput"
            "ELAN9038:00 04F3:261A",
            "ELAN9038:00 04F3:261A Stylus Pen (0)",
        },
        output = "eDP1", -- from "xrandr"
        timeout = 6000, -- timeout of the popup in milliseconds
    },
    touchpad = "ETPS/2 Elantech Touchpad", -- from "xinput" or nil
    terminal = "kitty",
    theme = "lines",
}

if settings.has_network then
    if settings.use_nm_applet then
        awful.spawn.with_shell("nm-applet")
    else
        settings.draw_network_widget = true
    end
end 

-- start compositor
-- picom sometimes crashes on rotate so we need to restart it
local function start_picom()
    awful.spawn.easy_async_with_shell("killall picom; sleep 1; picom", function(s,e,reason,code)
        if reason == "signal" and code == 11 then
            start_picom()
        end
    end)
end
start_picom()
-- and screen locker
awful.spawn("light-locker --lock-after-screensaver=900", false) -- lock after 15 minutes
-- autohide mouse
awful.spawn("unclutter", false)
-- start clipboard manager
awful.spawn("copyq", false)
-- start volume control
awful.spawn("mate-volume-control-status-icon", false)
-- start bluetooth control
if settings.has_bluetooth then
    awful.spawn("blueman-applet", false)
end
-- start touch keyboard and gesture recognition
if settings.has_touchscreen then
    awful.spawn.with_shell("ps cax | grep onboard || onboard")
    awful.spawn("touchegg", false)
end
awful.spawn("/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1", false)

-- test if not nil
if settings.touchpad ~= nil then 
    local options = {}
    options["libinput Tapping Enabled"] = 1
    options["libinput Natural Scrolling Enabled"] = 1

    for k,v in pairs(options) do
        awful.spawn.easy_async_with_shell("xinput set-prop '" .. settings.touchpad .. "' '" .. tostring(k) .. "' " .. tostring(v))
    end
end

-- init the theme
local beautiful = require("beautiful")
beautiful.init(require("themes." .. settings.theme .. "-theme"))
local selected_theme = require(settings.theme)
selected_theme.setup()

-- init keys/buttons
require("keys")

-- transfer focus to next window on close
require("awful.autofocus")

client.connect_signal("manage", function(c)
    -- don't place clients outside the screen
    if awesome.startup and not c.size_hints.user_position and not c.size_hints.program_position then
        awful.placement.no_offscreen(c)
    end
    c.single_tag = true -- set the default gui mode to single tag
end)

-- start autorotate
local autorotate = require("components.autorotate")
if settings.has_touchscreen then
    autorotate.setup {
        indev = settings.ts_rotate.indev,
        output = settings.ts_rotate.output,
        timeout = settings.ts_rotate.timeout,
    }
end
