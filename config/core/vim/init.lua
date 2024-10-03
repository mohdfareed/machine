-- bootstrap lazy.nvim plugin manager
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
	vim.fn.system({
		"git",
		"clone",
		"--filter=blob:none",
		"https://github.com/folke/lazy.nvim.git",
		"--branch=stable",
		lazypath,
	})
end
vim.opt.rtp:prepend(vim.env.LAZY or lazypath)

local lazy_config = { -- plugins manager config
	checker = { enabled = true }, -- check for updates on startup
	install = { colorscheme = { "onedark" } }, -- startup installation theme
	ui = { border = "rounded" }, -- use rounded borders
}

require("lazy").setup({ -- load plugins
	-- add LazyVim and import its plugins
	{ "LazyVim/LazyVim", import = "lazyvim.plugins" },

	-- import extras modules
	{ import = "lazyvim.plugins.extras.vscode" },
	{ import = "lazyvim.plugins.extras.coding.copilot" },

	-- disabled plugins
	{ "goolord/alpha-nvim", enabled = false },
	{ "akinsho/bufferline.nvim", enabled = false },
	{ "echasnovski/mini.indentscope", enabled = false },

	-- import custom plugins
	{ import = "plugins" },
}, lazy_config)
