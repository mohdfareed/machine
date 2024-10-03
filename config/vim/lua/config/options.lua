-- default options
-- https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
require('config.utils')

vim.opt.guicursor = 'n-v-c:hor25,i-ci:ver25,r-cr:block,n:blinkon250'
vim.opt.scrolloff = 8 -- keep 8 lines above/below cursorline

if not vim.g.vscode then
  vim.opt.colorcolumn = '80' -- show 80 chars column
  vim.opt.colorcolumn = '120' -- show 120 chars column
  vim.opt.listchars:append 'space:⋅' -- show spaces
  vim.opt.spell = true -- enable spell checker

  -- code folding
  vim.o.foldlevel = 99
  vim.o.foldlevelstart = 99
  vim.o.foldenable = true
  vim.o.fillchars = [[eob: ,fold: ,foldopen:,foldsep: ,foldclose:]]

  -- indentation
  vim.opt.tabstop = 4
  vim.opt.softtabstop = 4
  vim.opt.shiftwidth = 4
  vim.opt.expandtab = true
  vim.opt.breakindent = true
end
