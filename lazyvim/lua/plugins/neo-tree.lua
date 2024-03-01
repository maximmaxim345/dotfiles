return {
  {
    "s1n7ax/nvim-window-picker",
    version = "2.*",
    config = function()
      require("window-picker").setup({
        filter_rules = {
          include_current_win = false,
          autoselect_one = true,
          -- filter using buffer options
          bo = {
            -- if the file type is one of following, the window will be ignored
            filetype = { "neo-tree", "neo-tree-popup", "notify" },
            -- if the buffer type is one of following, the window will be ignored
            buftype = { "terminal", "quickfix" },
          },
        },
      })
    end,
  },
  {
    "nvim-neo-tree/neo-tree.nvim",
    optional = true,
    keys = function(_, keys)
      local Util = require("lazyvim.util")
      local override = {
        {
          "<leader>fE",
          function()
            require("neo-tree.command").execute({ toggle = true, dir = Util.root() })
          end,
          desc = "Explorer NeoTree (root dir)",
        },
        {
          "<leader>fe",
          function()
            require("neo-tree.command").execute({ toggle = true, dir = vim.loop.cwd() })
          end,
          desc = "Explorer NeoTree (cwd)",
        },
        { "<leader>e", "<leader>fe", desc = "Explorer NeoTree (root dir)", remap = true },
        { "<leader>E", "<leader>fE", desc = "Explorer NeoTree (cwd)", remap = true },
      }
      for i, key in ipairs(keys) do
        for _, over in ipairs(override) do
          if key[1] == over[1] then
            keys[i] = over
            break
          end
        end
      end
    end,
    opts = function(_, opts)
      opts.window.mappings["-"] = "split_with_window_picker"
      opts.window.mappings["|"] = "vsplit_with_window_picker"
      opts.window.mappings["<CR>"] = "open_drop"
      opts.window.mappings["<S-CR>"] = "open_with_window_picker"

      local events = require("neo-tree.events")
      opts.event_handlers = opts.event_handlers or {}

      vim.list_extend(opts.event_handlers, {
        {
          event = events.FILE_OPENED,
          handler = function(file_path)
            require("neo-tree.command").execute({ action = "close" })
          end,
        },
      })
    end,
  },
}
