local theme = {}
local themes_path = require("gears.filesystem").get_themes_dir()
local path = require("gears.filesystem").get_configuration_dir()
local dpi = require("beautiful.xresources").apply_dpi
local gears = require("gears")

-- colors

theme.slider_fg = "#DAE7E2"
theme.slider_fg_inactive = "#DAE7E270"
theme.slider_bg = "#FFFFFF87"

theme.fg_normal  = "#FFFFFF"
theme.bg_normal = "#FFFFFF4D"

theme.titlebar_bg_normal = "#748c82"
theme.titlebar_bg_focus  = "#92B0A4"

theme.border_normal = "#4D4D4D4D"
theme.border_focus = "#92B0A4"
theme.border_marked = "#92B0A4"
theme.bg_accent = "#3E8978"
theme.bg_systray = theme.bg_accent

theme.button_hover_active = "#3E8978"
theme.button_hover_inactive = "#92B0A4"
theme.button_active = "#3E8978bb"
theme.button_inactive = "#92B0A4bb"

theme.dashboard_bg = "#00000040"
theme.dashboard_panel_color = "#59907B"

-- sizes

theme.useless_gap   = dpi(5)
theme.bar_size = dpi(30)
theme.dashboard_size = dpi(700)
theme.gap_single_client = false
theme.interactive_border_width = dpi(10)

-- notifications
theme.notification_bg = "#59907BA0"
theme.notification_fg = "#FFFFFF"
theme.notification_border_color = "transparent"
theme.notification_border_width = 0
theme.notification_shape = function(cr, width, height)
    gears.shape.rounded_rect(cr, width, height, theme.bar_size / 2)
end

-- autorotate
theme.autorotate_shape = gears.shape.circle
theme.autorotate_bg = theme.bg_accent
theme.autorotate_margin = dpi(30)

-- fonts

theme.font      = "sans 12"
theme.applist_font = "sans 12"
theme.slider_font = "sans 12"
theme.menu_font = "sans 10"
theme.menu_font_large = "sans 20"

-- wallpaper

theme.wallpaper = path .. "wallpaper/lines-arch.png"

-- icons

local icons = path .. "icons/lines/"

theme.start_menu_icon = icons .. "start-menu.png"
theme.titlebar_close_button_focus  = icons .. "button-close.png"
theme.titlebar_close_button_normal = icons .. "button-inactive.png"
theme.titlebar_minimize_button_focus  = icons .. "button-minimize.png"
theme.titlebar_minimize_button_normal = icons .. "button-inactive.png"
theme.titlebar_maximized_button_focus_active = icons .. "button-maximize-active.png"
theme.titlebar_maximized_button_focus_inactive = icons .. "button-maximize.png"
theme.titlebar_maximized_button_normal_active = icons .. "button-inactive.png"
theme.titlebar_maximized_button_normal_inactive = icons .. "button-inactive.png"
theme.titlebar_ontop_button_focus_active = icons .. "button-ontop-active.png"
theme.titlebar_ontop_button_focus_inactive = icons .. "button-ontop.png"
theme.titlebar_ontop_button_normal_active = icons .. "button-inactive.png"
theme.titlebar_ontop_button_normal_inactive = icons .. "button-inactive.png"
theme.titlebar_sticky_button_focus_active = icons .. "button-sticky-active.png"
theme.titlebar_sticky_button_focus_inactive = icons .. "button-sticky.png"
theme.titlebar_sticky_button_normal_active = icons .. "button-inactive.png"
theme.titlebar_sticky_button_normal_inactive = icons .. "button-inactive.png"
theme.titlebar_floating_button_focus_active = icons .. "button-floating-active.png"
theme.titlebar_floating_button_focus_inactive = icons .. "button-floating.png"
theme.titlebar_floating_button_normal_active = icons .. "button-inactive.png"
theme.titlebar_floating_button_normal_inactive = icons .. "button-inactive.png"

theme.battery_100 = icons .. "battery-100.png"
theme.battery_80 = icons .. "battery-80.png"
theme.battery_60 = icons .. "battery-60.png"
theme.battery_40 = icons .. "battery-40.png"
theme.battery_20 = icons .. "battery-20.png"
theme.battery_0 = icons .. "battery-0.png"
theme.battery_charging = icons .. "battery-charging.png"

theme.layout_tile = icons .. "mode-tile.png"
theme.layout_tiletop = icons .. "mode-tile-top.png"
theme.layout_magnifier = icons .. "mode-magnifier.png"
theme.layout_floating = icons .. "mode-floating.png"

theme.wifi_1 = icons .. "wifi-1.png"
theme.wifi_2 = icons .. "wifi-2.png"
theme.wifi_3 = icons .. "wifi-3.png"
theme.wifi_4 = icons .. "wifi-4.png"
theme.ethernet = icons .. "ethernet.png"

theme.brightness_slider_icon = icons .. "brightness.png"
theme.volume_slider_icon = icons .. "volume.png"
theme.volume_slider_muted_icon = icons .. "volume-muted.png"

theme.power_off = icons .. "power-off.png"
theme.reboot = icons .. "reboot.png"
theme.logout = icons .. "logout.png"

theme.autorotate_icon = icons .. "reboot.png"

return theme
