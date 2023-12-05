-- Pull in the wezterm API
local wezterm = require("wezterm")

-- This table will hold the configuration.
local config = {}

-- In newer versions of wezterm, use the config_builder which will
-- help provide clearer error messages
if wezterm.config_builder then
	config = wezterm.config_builder()
end

-- This is where you actually apply your config choices

config.launch_menu = {}

-- Function to add distroboxes to the launcher (given the output of `distrobox list --no-color`)
local function addDistroBoxesToLauncher(distroboxList)
	-- Split the distrobox list into lines
	local lines = {}
	for line in distroboxList:gmatch("[^\r\n]+") do
		table.insert(lines, line)
	end

	-- Remove the header line
	table.remove(lines, 1)

	-- Iterate over the lines and add distroboxes to the launch_menu
	for _, line in ipairs(lines) do
		local id, name = line:match("(%w+)%s+%|%s+(%S+)")
		if id and name then
			table.insert(config.launch_menu, {
				label = name,
				args = { "distrobox", "enter", id },
			})
		end
	end
end

-- Add distrboxes to the launcher

local filepath = "/.flatpak-info"

function file_exists(name)
	local f = io.open(name, "r")
	if f ~= nil then
		io.close(f)
		return true
	else
		return false
	end
end

-- test if we are not on linux
if not wezterm.target_triple:find("linux") then
	return config
elseif file_exists(filepath) then
	local success, stdout, stderr =
		wezterm.run_child_process({ "flatpak-spawn", "--host", "distrobox", "list", "--no-color" })
	if success then
		addDistroBoxesToLauncher(stdout)
	end
else
	local success, stdout, stderr = wezterm.run_child_process({ "distrobox", "list", "--no-color" })
	if success then
		addDistroBoxesToLauncher(stdout)
	end
end

config.use_dead_keys = false
config.use_fancy_tab_bar = true

local function scheme_for_appearance(appearance)
	if appearance:find("Dark") then
		return "Catppuccin Mocha"
	else
		return "Catppuccin Latte"
	end
end

config.color_scheme = scheme_for_appearance(wezterm.gui.get_appearance())

-- For example, changing the color scheme:
config.font = wezterm.font("FiraCode Nerd Font")

-- and finally, return the configuration to wezterm
return config
