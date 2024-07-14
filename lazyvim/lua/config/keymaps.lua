-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

vim.keymap.set("i", "jk", "<Esc>")
vim.keymap.set("i", "<C-BS>", "<C-W>")
vim.keymap.set("i", "<C-H>", "<C-W>")
vim.keymap.set("i", "<S-Tab>", "<C-d>")

vim.keymap.set("n", "<c-/>", function()
  LazyVim.terminal()
end, { desc = "Terminal (cwd)" })

if not vim.g.vscode then
  local wk = require("which-key")
  wk.add({
    { "<c-q>", "<leader>bd", desc = "Close buffer", remap = true },
    { "<leader>b<Left>", "<cmd>BufferLineMovePrev<cr>", desc = "Move buffer to left" },
    { "<leader>b<Right>", "<cmd>BufferLineMoveNext<cr>", desc = "Move buffer to right" },
    { "<leader>cc", group = "Copilot" },
    { "<leader>ccd", ":Copilot disable<CR>", desc = "Disable copilot" },
    { "<leader>cce", ":Copilot enable<CR>", desc = "Enable copilot" },
    { "<leader>ccf", group = "File specific settings" },
    { "<leader>ccfd", ":let b:copilot_enabled=v:false<CR>", desc = "Disable copilot for the current file" },
    { "<leader>ccfe", ":let b:copilot_enabled=v:true<CR>", desc = "Enable copilot for the current file" },
    { "<leader>uN", group = "Neoscroll" },
  }, {
    mode = "n",
  })
end

vim.api.nvim_set_keymap("x", "<leader>p", '"_dP', { noremap = true, silent = true })

-- wk.register({
--   -- Copilot
--   ["<M-c>"] = {
--     name = "Copilot",
--     ["<M-c>"] = { 'copilot#Accept("")', "Accept copilot suggestion", expr = true },
--     n = { "<Plug>(copilot-next)", "Next copilot suggestion", noremap = false },
--     p = { "<Plug>(copilot-previous)", "Previous copilot suggestion", noremap = false },
--     ["<ESC>"] = { "<Plug>(copilot-dismiss)", "Dismiss copilot suggestion", noremap = false },
--     -- space
--     ["<Space>"] = { "<ESC>:Copilot panel<CR>", "Open copilot panel" },
--   },
-- }, {
--   mode = "i",
-- })

-- -- Macros for bettter markdown/LaTeX editing (for qwertz keyboard layout)
-- vim.api.nvim_set_keymap("i", "jt", "$$<ESC>i", {})
-- vim.api.nvim_set_keymap("i", "jT", "$$<CR>$$<ESC>O", {})
-- vim.api.nvim_set_keymap("i", "jß", "\\", {})
-- vim.api.nvim_set_keymap("i", "jö", "\\", {})
-- vim.api.nvim_set_keymap("i", "j7", "{", {})
-- vim.api.nvim_set_keymap("i", "j0", "}", {})
-- vim.api.nvim_set_keymap("i", "jc", "`", {})
-- vim.api.nvim_set_keymap("i", "jC", "```", {})
-- vim.api.nvim_set_keymap("i", "jB", "\\{\\}<ESC>hi", {})
