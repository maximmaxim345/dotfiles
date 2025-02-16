return {
  -- {
  --   "karb94/neoscroll.nvim",
  --   config = function()
  --     require("neoscroll").setup({
  --       mappings = { "<C-y>", "<C-e>", "zt", "zz", "zb" },
  --       hide_cursor = true,
  --       stop_eof = true,
  --       respect_scrolloff = false,
  --       cursor_scrolls_alone = true,
  --       easing_function = "quadratic",
  --       performance_mode = false,
  --       time = 100,
  --     })
  --     local t = {}
  --     t["<C-u>"] = { "scroll", { "-vim.wo.scroll", "true", "150" } }
  --     t["<C-d>"] = { "scroll", { "vim.wo.scroll", "true", "150" } }
  --     require("neoscroll.config").set_mappings(t)
  --   end,
  --   cond = not vim.g.neovide, -- neovide has its own scrolling
  --   lazy = false,
  --   keys = {
  --     { "<leader>uNp", "<cmd>NeoscrollEnableGlobalPM<CR>", desc = "Enable performance mode" },
  --     { "<leader>uNP", "<cmd>NeoscrollDisableGlobalPM<CR>", desc = "Disable performance mode" },
  --   },
  -- },
  {
    "anuvyklack/windows.nvim",
    dependencies = {
      "anuvyklack/middleclass",
      {
        "anuvyklack/animation.nvim",
        enabled = false, -- not vim.g.neovide,
      },
    },
    config = function()
      vim.o.winwidth = 10
      vim.o.winminwidth = 10
      vim.o.equalalways = false
      require("windows").setup({
        ignore = {
          filetype = { "NvimTree", "neo-tree", "undotree", "gundo", "no-neck-pain" },
        },
      })
    end,
    lazy = false,
    keys = {
      { "<leader>bm", "<cmd>WindowsMaximize<CR>", desc = "Maximize buffer" },
      { "<leader>bE", "<cmd>WindowsEqualize<CR>", desc = "Equalize size of buffers" },
      { "<leader>ba", "<cmd>WindowsToggleAutowidth<CR>", desc = "Toggle autowidth" },
    },
  },
  {
    "sindrets/winshift.nvim",
    config = function()
      -- Lua
      require("winshift").setup({
        highlight_moving_win = true, -- Highlight the window being moved
        focused_hl_group = "Visual", -- The highlight group used for the moving window
        moving_win_options = {
          -- These are local options applied to the moving window while it's
          -- being moved. They are unset when you leave Win-Move mode.
          wrap = false,
          cursorline = false,
          cursorcolumn = false,
          colorcolumn = "",
        },
        keymaps = {
          disable_defaults = false, -- Disable the default keymaps
          win_move_mode = {
            ["h"] = "left",
            ["j"] = "down",
            ["k"] = "up",
            ["l"] = "right",
            ["H"] = "far_left",
            ["J"] = "far_down",
            ["K"] = "far_up",
            ["L"] = "far_right",
            ["<left>"] = "left",
            ["<down>"] = "down",
            ["<up>"] = "up",
            ["<right>"] = "right",
            ["<S-left>"] = "far_left",
            ["<S-down>"] = "far_down",
            ["<S-up>"] = "far_up",
            ["<S-right>"] = "far_right",
          },
        },
        ---A function that should prompt the user to select a window.
        ---
        ---The window picker is used to select a window while swapping windows with
        ---`:WinShift swap`.
        ---@return integer? winid # Either the selected window ID, or `nil` to
        ---   indicate that the user cancelled / gave an invalid selection.
        window_picker = function()
          return require("winshift.lib").pick_window({
            -- A string of chars used as identifiers by the window picker.
            picker_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
            filter_rules = {
              -- This table allows you to indicate to the window picker that a window
              -- should be ignored if its buffer matches any of the following criteria.
              cur_win = true, -- Filter out the current window
              floats = true, -- Filter out floating windows
              filetype = {}, -- List of ignored file types
              buftype = {}, -- List of ignored buftypes
              bufname = {}, -- List of vim regex patterns matching ignored buffer names
            },
            ---A function used to filter the list of selectable windows.
            ---@param winids integer[] # The list of selectable window IDs.
            ---@return integer[] filtered # The filtered list of window IDs.
            filter_func = nil,
          })
        end,
      })
    end,
    keys = {
      { "<C-w><C-s>", "<cmd>WinShift swap<CR>", desc = "Swap buffer" },
      { "<C-w><C-w>", "<cmd>WinShift<CR>", desc = "Move buffer" },
    },
  },
  -- {
  --   "shortcuts/no-neck-pain.nvim",
  --   config = function()
  --     require("no-neck-pain").setup({
  --       width = 200,
  --     })
  --   end,
  --   keys = {
  --     { "<leader>bn", "<cmd>NoNeckPain<CR>", desc = "Toggle no-neck-pain" },
  --   },
  -- },
  {
    "folke/edgy.nvim",
    optional = true,
    event = "VeryLazy",
    opts = function(_, opts)
      opts.animate = {
        enabled = false,
      }
    end,
    {
      "smoka7/multicursors.nvim",
      event = "VeryLazy",
      dependencies = {
        "nvimtools/hydra.nvim",
      },
      opts = {},
      cmd = { "MCstart", "MCvisual", "MCclear", "MCpattern", "MCvisualPattern", "MCunderCursor" },
      keys = {
        {
          mode = { "v", "n" },
          "<Leader>m",
          "<cmd>MCstart<cr>",
          desc = "Create a selection for selected text or word under the cursor",
        },
      },
    },
  },
}
