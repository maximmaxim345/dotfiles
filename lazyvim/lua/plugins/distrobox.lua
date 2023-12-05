DISTROBOX = {}

-- save the current container
local restart_request = os.getenv("NEOVIDE_RESTART_REQUEST_FILE")
if restart_request ~= nil then
  -- read the file
  local file = io.open(restart_request, "r")
  DISTROBOX.current = file:read("*all")
end

function DISTROBOX.launch_selector()
  local targets = DISTROBOX.get_launch_targets()
  local opts = {
    scroll_strategy = "cycle",
    layout_strategy = "center",
    initial_mode = "insert", -- normal
    previewer = false,
  }
  local bufnr = vim.api.nvim_get_current_buf()
  local p = vim.api.nvim_buf_get_name(bufnr)
  local picker = require("telescope.pickers").new(opts, {
    results_title = "Restart neovim",
    prompt_title = "Select where to restart",
    finder = require("telescope.finders").new_table({
      results = targets,
    }),
    sorter = require("telescope.config").values.generic_sorter(opts),
    attach_mappings = function(prompt_bufnr, map)
      -- map default actions
      require("telescope.actions").select_default:replace(function()
        local selection = require("telescope.actions.state").get_selected_entry()
        DISTROBOX.restart(selection.value)
        require("telescope.actions").close(prompt_bufnr)
      end)
      return true
    end,
  })
  picker:find()
end

function DISTROBOX.get_launch_targets()
  -- distrobox-list --no-color gives this output:
  -- ID           | NAME                 | STATUS                         | IMAGE
  -- 1c1d1b256f18 | ubuntu               | Up About an hour               | localhost/dbi_ubuntu:latest
  -- f8edd62c5c4a | xilinx               | Exited (143) 2 days ago        | localhost/dbi_xilinx:latest

  -- we only need the NAME column
  local targets = {}
  local cmd = "distrobox-list --no-color"
  local handle = io.popen(cmd)
  local result = handle:read("*a")
  handle:close()
  for line in result:gmatch("[^\r\n]+") do
    if line:match("^ID") then
      -- skip the header
      goto continue
    end
    local name = line:match("|%s*(%S+)%s*|")
    if name ~= nil then
      table.insert(targets, name)
    end
    ::continue::
  end
  -- add HOST (the host machine)
  table.insert(targets, "HOST")
  -- remove the current one
  for i, v in ipairs(targets) do
    if v == DISTROBOX.current then
      table.remove(targets, i)
      break
    end
  end
  return targets
end

function DISTROBOX.restart(target)
  local restart_request = os.getenv("NEOVIDE_RESTART_REQUEST_FILE")
  if restart_request ~= nil then
    -- read the file
    local file = io.open(restart_request, "w")
    file:write(target)
    file:close()
    vim.cmd("qa!") -- just quit
  end
end

-- Helper functions for distrobox integration
return {
  {
    "goolord/alpha-nvim",
    optional = true,
    opts = function(_, dashboard)
      -- distrobox integration
      local restart_request = os.getenv("NEOVIDE_RESTART_REQUEST_FILE")
      if restart_request ~= nil then
        -- read the file
        local file = io.open(restart_request, "r")
        local current = file:read("*all")

        local button = dashboard.button("d", "Open Distrobox selector", ":lua DISTROBOX.launch_selector()<CR>")
        button.opts.hl = "AlphaButtons"
        button.opts.hl_shortcut = "AlphaShortcut"
        table.insert(dashboard.section.buttons.val, 2, button)
      end
    end,
  },
}
