return {}

-- ConfigurePlugin(function()
--   local config = {
--     auto_install = false,
--     highlight = { enable = true },
--     indent = { enable = true },
--     ensure_installed = {
--       'vim',
--       'regex',
--       'bash',
--       'markdown',
--       'markdown_inline',
--       'lua',
--       'python'
--     },
--   }
--
--   -- enable syntax based code folding
--   -- vim.opt.foldmethod = 'expr'
--   -- vim.opt.foldexpr = 'nvim_treesitter#foldexpr()'
--   -- vim.opt.foldlevelstart = 99
--   require('nvim-treesitter.configs').setup(config)
-- end)
--
-- return {
--   {
--     'nvim-treesitter/nvim-treesitter',
--     cmd = { "TSUpdateSync" },
--     dependencies = {
--       'nvim-treesitter/nvim-treesitter-textobjects',
--       'nvim-treesitter/nvim-treesitter-context',
--     },
--     build = ':TSUpdate',
--     cond = function() return not vim.g.vscode end,
--   },
-- }
--
