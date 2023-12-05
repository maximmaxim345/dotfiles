local p = {
  {
    "marko-cerovac/material.nvim",
  },
  {
    "bluz71/vim-moonfly-colors",
  },
  {
    "folke/tokyonight.nvim",
  },
  {
    "shaunsingh/nord.nvim",
  },
  {
    "projekt0n/github-nvim-theme",
  },
  {
    "jesseleite/nvim-noirbuddy",
    dependencies = { "tjdevries/colorbuddy.nvim", branch = "dev" },
  },
  {
    "uloco/bluloco.nvim",
    dependencies = { "rktjmp/lush.nvim" },
  },
  {
    "maxmx03/fluoromachine.nvim",
  },
  { "catppuccin/nvim", name = "catppuccin" },
}

-- disable lazy in all colorscheme plugins
for _, plugin in ipairs(p) do
  plugin.lazy = false
end

return p
