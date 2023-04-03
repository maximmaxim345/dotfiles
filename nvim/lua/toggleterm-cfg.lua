
local default_shell = vim.o.shell
if vim.fn.has("win64") == 1 or vim.fn.has("win32") == 1 then
    default_shell = "powershell.exe"
end
require("toggleterm").setup{
  hide_numbers = true, -- hide the number column in toggleterm buffers
  shade_filetypes = {},
  shade_terminals = true,
  start_in_insert = true,
  insert_mappings = false,
  persist_size = true,
  direction = 'horizontal',
  close_on_exit = true, -- close the terminal window when the process exits
  shell = default_shell,
  -- This field is only relevant if direction is set to 'float'
  float_opts = {
    -- The border key is *almost* the same as 'nvim_win_open'
    -- see :h nvim_win_open for details on borders however
    -- the 'curved' border is a custom border type
    -- not natively supported but implemented in this plugin.
    border = 'double',
    width = function() return math.floor(vim.o.columns * 0.9) end,
    height = function() return math.floor(vim.o.lines * 0.9) end,
    winblend = 10,
  },
  highlights = {
      Normal = {
          guibg = "Normal" -- this somehow sets keeps the background color
      },
      NormalFloat = {
          link = "Normal"
      },
      FloatBorder = {
          link = "NormalFloat"
      }
  },
  open_mapping = "<M-t>"
}
