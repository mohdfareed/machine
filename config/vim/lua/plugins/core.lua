return {
  { -- one dark theme
    'navarasu/onedark.nvim',
    config = function()
      require('onedark').setup({
        transparent = true,
        lualine = { transparent = true },
        highlights = {
          NormalFloat = { bg = 'none' },
          FloatBorder = { bg = 'none' },
        }
      })
      require('onedark').load()
    end,
  },

  { -- file explorer
    'nvim-neo-tree/neo-tree.nvim',
    opts = {
      window = { position = "float" },
      popup_border_style = 'rounded',
    },
  },

  { -- git editor utilities
    'lewis6991/gitsigns.nvim',
    opts = {
      preview_config = { border = 'rounded' },
    },
  },

  { -- auto-completion
    'saghen/blink.cmp',
    opts = {
      completion = {
        documentation = { window = { border = "rounded" } },
        menu = {
          border = "rounded",
          winhighlight = "Normal:Normal,FloatBorder:FloatBorder",
        },
      },
    }
  },

  { -- hover documentation
    "folke/noice.nvim",
    opts = {
      presets = { lsp_doc_border = true },
    },
  },

  { -- keybinds window
    'folke/which-key.nvim',
    opts = {
      win = { border = 'rounded' },
    },
  },
}
