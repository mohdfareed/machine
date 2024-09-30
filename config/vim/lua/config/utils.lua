CreateGroup = vim.api.nvim_create_augroup   -- Create autocmd group.
CreateAutocmd = vim.api.nvim_create_autocmd -- Create autocmd.

-- Create a keymap group.
function RegisterGroup(bind, name)
  local ok, whichkey = pcall(require, 'which-key')
  if ok then
    whichkey.add({ { bind, group = name } })
  end
end

-- Map a keybind.
function MapKey(mode, l, r, desc, opts)
  opts = opts or {}
  opts.desc = desc
  vim.keymap.set(mode, l, r, opts)
end
