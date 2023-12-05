-- Create Popup menu
vim.cmd([[
aunmenu PopUp
vnoremenu PopUp.Cut                         "+x
vnoremenu PopUp.Copy                        "+y
anoremenu PopUp.Paste                       "+gP
vnoremenu PopUp.Paste                       "+P
vnoremenu PopUp.Delete                      "_x
nnoremenu PopUp.Select\ All                 ggVG
vnoremenu PopUp.Select\ All                 gg0oG$
inoremenu PopUp.Select\ All                 <C-Home><C-O>VG

anoremenu PopUp.-1-                         <Nop>

" Lsp Options
nnoremenu PopUp.Code\ Action                <Cmd>lua vim.lsp.buf.code_action()<CR>
nnoremenu PopUp.Go\ To\ Definition          <Cmd>Telescope lsp_definitions<CR>
nnoremenu PopUp.Peek\ Definition            <Cmd>Lspsaga peek_definition<CR>
nnoremenu PopUp.Open\ Documentation         <Cmd>Lspsaga hover_doc<CR>
nnoremenu PopUp.Open\ Definitions           <Cmd>Lspsaga finder<CR>
nnoremenu PopUp.Rename\ Symbol              <Cmd>Lspsaga rename<CR>
nnoremenu PopUp.Format\ File                <Cmd>lua vim.lsp.buf.format({async=true})<CR>
nnoremenu PopUp.Toggle\ Workspace\ Diagnostics  <Cmd>TroubleToggle workspace_diagnostics<CR>
nnoremenu PopUp.Diagnostic\ Next            <Cmd>lua vim.lsp.diagnostic.goto_next()<CR>

vnoremenu PopUp.Format\ Range               <Cmd>lua vim.lsp.buf.range_formatting()<CR>

inoremenu PopUp.Code\ Action                <Esc><Cmd>lua vim.lsp.buf.code_action()<CR>
inoremenu PopUp.Go\ To\ Definition          <Esc><Cmd>Telescope lsp_definitions<CR>
inoremenu PopUp.Peek\ Definition            <Esc><Cmd>Lspsaga peek_definition<CR>
inoremenu PopUp.Open\ Documentation         <Esc><Cmd>Lspsaga hover_doc<CR>
inoremenu PopUp.Open\ Definitions           <Esc><Cmd>Lspsaga finder<CR>
inoremenu PopUp.Rename\ Symbol              <Esc><Cmd>Lspsaga rename<CR>
inoremenu PopUp.Format\ File                <Esc><Cmd>lua vim.lsp.buf.format({async=true})<CR>
inoremenu PopUp.Toggle\ Workspace\ Diagnostics  <Esc><Cmd>TroubleToggle workspace_diagnostics<CR>
inoremenu PopUp.Diagnostic\ Next            <Esc><Cmd>lua vim.lsp.diagnostic.goto_next()<CR>

anoremenu PopUp.-2-                         <Nop>

" Buffer Opetions
nnoremenu PopUp.Close\ Buffer               <C-w>c<CR>
nnoremenu PopUp.Split\ Buffer               <C-w>s<CR>
nnoremenu PopUp.Vsplit\ Buffer              <C-w>v<CR>
vnoremenu PopUp.Close\ Buffer               <C-w>c<CR>
vnoremenu PopUp.Split\ Buffer               <C-w>s<CR>
vnoremenu PopUp.Vsplit\ Buffer              <C-w>v<CR>
inoremenu PopUp.Close\ Buffer               <Esc><C-w>c<CR>
inoremenu PopUp.Split\ Buffer               <Esc><C-w>s<CR>
inoremenu PopUp.Vsplit\ Buffer              <Esc><C-w>v<CR>

]])

return {}
