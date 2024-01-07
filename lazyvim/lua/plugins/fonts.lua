-- helper functions for setting fonts and their sizes

GUIFONT = {} -- global variable, not fancy but it works

-- function to change font size
function GUIFONT.set_font_size(size, absolute)
  if absolute then
    GUIFONT.font_size = size
  else
    GUIFONT.font_size = GUIFONT.font_size + size
  end
  -- minimum font size
  if GUIFONT.font_size <= 3 then
    GUIFONT.font_size = 3
  end
  vim.o.guifont = "FiraCode Nerd Font:h" .. GUIFONT.font_size
end
-- set default font size and theme
function GUIFONT.set_default()
  GUIFONT.set_font_size(12, true)
end

GUIFONT.set_default()

return {}
