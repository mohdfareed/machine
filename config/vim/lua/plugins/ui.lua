return {
  { -- keybinds window
    'folke/which-key.nvim',
    opts = {
      window = { border = 'rounded' },
    },
  },

  { -- one dark theme
    'navarasu/onedark.nvim',
    lazy = false,
    priority = 1000,
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

  { -- statusline
    'nvim-lualine/lualine.nvim',
    opts = {
      options = {
        theme = 'onedark',
        component_separators = '|',
        section_separators = { left = '', right = '' },
      },
      sections = {
        lualine_y = { 'buffers', },
        lualine_z = { 'location', 'searchcount', 'selectioncount', },
      },
      extensions = {
        'lazy',
        'neo-tree',
        'nvim-dap-ui',
        'trouble',
        'toggleterm',
        'symbols-outline',
        'man',
      },
    },
  },
}
