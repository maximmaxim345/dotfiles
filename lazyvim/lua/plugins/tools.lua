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
  {
    "uga-rosa/ccc.nvim",
    opts = {
      highlighter = {
        auto_enable = true,
      },
    },
    event = "VeryLazy",
    keys = {
      { "<leader>cC", "<cmd>CccPick<CR>", desc = "Open colorpicker (ccc)" },
    },
  },
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
    enabled = false,
    dependencies = "neovim/nvim-lspconfig",
    event = "VeryLazy",
    opts = {},
  },
  {
    "huggingface/llm.nvim",
    enabled = false,
    opts = {
      tokens_to_clear = { "<|endoftext|>" },
      debounce_ms = 1000,
      fim = {
        enabled = true,
        prefix = "<fim_prefix>",
        middle = "<fim_middle>",
        suffix = "<fim_suffix>",
      },
      backend = "ollama",
      url = "http://localhost:11434/api/generate",
      model = "starcoder2:3b",
      context_window = 4000, -- 8192,
      tokenizer = {
        repository = "bigcode/starcoder",
      },
      enable_suggestions_on_startup = false,
      accept_keymap = "<M-i>",
      dismiss_keymap = "<M-o>",
    },
  },
  {
    "folke/flash.nvim",
    keys = {
      {
        "/",
        mode = { "n", "x", "v" },
        function()
          require("flash").jump()
        end,
        desc = "Flash Jump",
      },
      {
        "?",
        mode = { "n", "x", "v" },
        function()
          require("flash").toggle(false)
          vim.api.nvim_feedkeys("?", "n", true)
        end,
        desc = "Normal backward search",
      },
    },
  },
}
