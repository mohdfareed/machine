-- default autocmds
-- https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
require("config.utils")

-- change cwd when launching a directory
if not vim.g.vscode then
  local auto_cd = CreateGroup('AutoCDOnEnter', { clear = true })
  CreateAutocmd('VimEnter', {
    group = auto_cd,
    callback = function()
      local arg = vim.fn.expand('<amatch>')
      if vim.fn.isdirectory(arg) == 1 then
        vim.cmd('cd ' .. arg)
      end
    end,
  })
end
