-- default keymaps:
-- https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
require('config.utils')

-- window management
MapKey('n', '<c-w>H', '<c-w>H', "Move window to the right")
MapKey('n', '<c-w>J', '<c-w>J', "Move window Down")
MapKey('n', '<c-w>K', '<c-w>K', "Move window Up")
MapKey('n', '<c-w>L', '<c-w>L', "Move window to the left")

-- center after jumping screen
MapKey('n', '<c-d>', '<c-d>zz', "Page down and center")
MapKey('n', '<c-u>', '<c-u>zz', "Page up and center")

if not vim.g.vscode then
  -- harpoon
  RegisterGroup('<leader>h', "Harpoon")
  MapKey('n', '<leader>h', Harpoon.open, "Menu")
  MapKey('n', '<leader>ha', Harpoon.mark.add_file, "Add file")
  MapKey('n', '<leader>hc', Harpoon.cmd_ui.toggle_quick_menu, "Commands")
  for i = 1, 4 do -- show only 4 marks
    MapKey('n', '<leader>' .. i, Harpoon.goto_file(i), "Goto mark " .. i)
  end

  -- code folding
  MapKey('n', 'zR', UFO.openAllFolds, "Open all folds")
  MapKey('n', 'zM', UFO.closeAllFolds, "Close all folds")
  MapKey('n', 'zr', UFO.openFoldsExceptKinds, "Open all folds except kinds")
  MapKey('n', 'zm', UFO.closeFoldsWith, "Close all folds with kinds")

  -- file explorer
  MapKey('n', '<leader>fe', NeoTree.toggle, "File explorer (root)")
  MapKey('n', '<leader>fE', NeoTree.toggle_cwd, "File explorer (cwd)")
end

-- groups renames
RegisterGroup('g', "Goto")
RegisterGroup('[', "Previous")
RegisterGroup(']', "Next")
