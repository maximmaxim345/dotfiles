-- It is not generally possible to detect if we run in a gui or not,
-- therefore we always bind the keys for font size changes
vim.api.nvim_set_keymap(
  "n",
  "<C-+>",
  ":lua GUIFONT.set_font_size(1)<CR>",
  { noremap = true, silent = true, desc = "Increase Font size" }
)
vim.api.nvim_set_keymap(
  "n",
  "<C-->",
  ":lua GUIFONT.set_font_size(-1)<CR>",
  { noremap = true, silent = true, desc = "Decrease Font size" }
)

-- Exit if not in neovide
if vim.g.neovide == nil then
  return {}
end

vim.api.nvim_set_keymap(
  "n",
  "<F11>",
  ":lua vim.g.neovide_fullscreen = not vim.g.neovide_fullscreen<CR>",
  { noremap = true, silent = true, desc = "Toggle Fullscreen" }
)

return {}
