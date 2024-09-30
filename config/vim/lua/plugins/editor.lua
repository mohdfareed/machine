return {
  { -- auto-detect indents
    'tpope/vim-sleuth',
  },

  { -- todo comments manager
    'folke/todo-comments.nvim',
    opts = { highlight = { keyword = 'fg' }, },
  },

  { -- code folding
    'kevinhwang91/nvim-ufo',
    dependencies = { 'kevinhwang91/promise-async' },
    config = function()
      require('ufo').setup({ -- default to syntax based
        provider_selector = function() return { 'treesitter', 'indent' } end
      })
    end,
    init = function()
      UFO = require('ufo')
    end,
  },

  { -- file explorer
    'nvim-neo-tree/neo-tree.nvim',
    opts = {
      popup_border_style = 'rounded',
      buffers = {
        follow_current_file = { enabled = true },
      },
      filesystem = {
        follow_current_file = { enabled = true },
      },
    },
    init = function()
      NeoTree = require('neo-tree')

      NeoTree.toggle = function()
        require("neo-tree.command").execute({
          toggle = true,
          position = 'float',
          dir = require("lazyvim.util").get_root()
        })
      end

      NeoTree.toggle_cwd = function()
        require("neo-tree.command").execute({
          toggle = true, position = 'float', dir = vim.loop.cwd()
        })
      end
    end
  },
}
