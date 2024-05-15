return {
  {
    "lambdalisue/suda.vim",
    lazy = true,
    cmd = { "SudaRead", "SudaWrite" },
  },
  {
    "NMAC427/guess-indent.nvim",
    opts = {},
    lazy = false,
    keys = {
      { "<leader>cI", "<cmd>GuessIndent<CR>", desc = "Guess indent" },
    },
  },
  {
    "TimUntersberger/neogit",
    lazy = true,
    cmd = { "Neogit" },
    dependencies = {
      "nvim-lua/plenary.nvim",
      {
        "sindrets/diffview.nvim",
        cmd = { "DiffviewOpen" },
        keys = {
          { "<leader>gd", "<cmd>DiffviewOpen<CR>", desc = "Open diffview" },
        },
      },
    },
    opts = {
      integrations = {
        diffview = true,
      },
    },
    keys = {
      { "<leader>gn", "<cmd>Neogit<CR>", desc = "Open Neogit" },
    },
  },
  {
    "willothy/flatten.nvim",
    opts = {},
    -- Ensure that it runs first to minimize delay when opening file from terminal
    lazy = false,
    priority = 1001,
  },
  {
    "mbbill/undotree",
    lazy = true,
    keys = {
      { "<leader>U", "<cmd>UndotreeToggle<CR>", desc = "Toggle undotree" },
    },
  },
  {
    "danymat/neogen",
    dependencies = "nvim-treesitter/nvim-treesitter",
    lazy = true,
    cmd = { "Neogen" },
    opts = {},
    keys = {
      { "<leader>cD", "<cmd>Neogen<CR>", desc = "Generate documentation" },
    },
  },
  -- {
  --   "uga-rosa/ccc.nvim",
  --   opts = {
  --     highlighter = {
  --       auto_enable = true,
  --     },
  --   },
  --   event = "VeryLazy",
  --   keys = {
  --     { "<leader>cC", "<cmd>CccPick<CR>", desc = "Open colorpicker (ccc)" },
  --   },
  -- },
  {
    "tpope/vim-fugitive",
    lazy = true,
    cmd = { "G", "Git", "Gdiffsplit", "Gwrite", "Gread", "Ggrep", "GMove", "GDelete", "GBrowse" },
  },
  {
    "LunarVim/bigfile.nvim",
    opts = {},
  },
  {
    "zeioth/garbage-day.nvim",
    enabled = true,
    dependencies = "neovim/nvim-lspconfig",
    event = "VeryLazy",
    opts = {},
  },
  {
    "folke/flash.nvim",
    keys = {
      {
        "/",
        mode = { "n", "x", "v" },
        function()
          require("flash").toggle(false)
          vim.api.nvim_feedkeys("/", "n", true)
        end,
        desc = "Search",
      },
      {
        "?",
        mode = { "n", "x", "v" },
        function()
          require("flash").toggle(true)
          vim.api.nvim_feedkeys("?", "n", true)
        end,
        desc = "Backward search (flash)",
      },
    },
  },
  {
    "zbirenbaum/copilot.lua",
    optional = true,
  },
}
