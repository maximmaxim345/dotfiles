local p = {
  { "ellisonleao/gruvbox.nvim" },
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
  { "Abstract-IDE/Abstract-cs" },
  { "rafamadriz/neon" },
  { "kyazdani42/blue-moon" },
  { "Tsuzat/NeoSolarized.nvim" },
  { "EdenEast/nightfox.nvim" },
  { "Mofiqul/adwaita.nvim" },
  { "xero/miasma.nvim" },
}

-- load all colorschemes
for _, plugin in ipairs(p) do
  -- plugin.lazy = false
  plugin.event = "VeryLazy"
end

return p
