return {
  { -- copilot
    'zbirenbaum/copilot.lua',
    opts = {
      filetypes = { ['*'] = true },
    },
  },

  { -- git editor utilities
    'lewis6991/gitsigns.nvim',
    opts = {
      preview_config = { border = 'rounded' },
    },
  },

  { -- harpoon
    'ThePrimeagen/harpoon',
    init = function()
      require('telescope').load_extension('harpoon')
      Harpoon = require('harpoon')
      Harpoon.ui = require('harpoon.ui')
      Harpoon.mark = require('harpoon.mark')
      Harpoon.term = require('harpoon.term')
      Harpoon.tmux = require('harpoon.tmux')
      Harpoon.cmd_ui = require('harpoon.cmd-ui')
      Harpoon.open = function() vim.cmd('Telescope harpoon marks') end
      Harpoon.goto_file = function(index)
        return function() Harpoon.ui.nav_file(index) end
      end
    end,
  },
}
