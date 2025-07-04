-- bootstrap lazy.nvim plugin manager
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
	local repo = "https://github.com/folke/lazy.nvim.git"
	local out = vim.fn.system({
		"git", "clone", "--filter=blob:none", "--branch=stable", repo, lazypath
	})

	if vim.v.shell_error ~= 0 then
		vim.api.nvim_echo({
			{ "Failed to clone lazy.nvim:\n", "ErrorMsg" },
			{ out,                            "WarningMsg" },
			{ "\nPress any key to exit..." },
		}, true, {})
		vim.fn.getchar()
		os.exit(1)
	end
end
vim.opt.rtp:prepend(vim.env.LAZY or lazypath)

local lazy_config = {
	checker = { enabled = true },           -- check for updates on startup
	install = { colorscheme = { "onedark" } }, -- startup installation theme
	ui = { border = "rounded" },            -- use rounded borders
}

require("lazy").setup({
	-- add LazyVim and import its plugins
	{ "LazyVim/LazyVim",         import = "lazyvim.plugins" },

	-- import custom plugins
	{ import = "plugins" },

	-- disabled plugins
	{ "akinsho/bufferline.nvim", enabled = false },
}, lazy_config)
