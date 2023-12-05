-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

-- change formatoptions on buffer enter

local formatOptions = vim.api.nvim_create_augroup("Format-Options", { clear = true })
vim.api.nvim_create_autocmd("BufEnter", {
  pattern = "*",
  command = "setlocal formatoptions-=c formatoptions-=o",
  group = formatOptions,
})
