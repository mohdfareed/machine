# =============================================================================
# MARK: Infrastructure
# =============================================================================

# Load public variables prepared by deployment.
set --local config_home (path dirname "$__fish_config_dir")
if test -f "$config_home/mc/env.fish"
    source "$config_home/mc/env.fish"
end

# =============================================================================
# MARK: Environment
# =============================================================================

# Activate Homebrew before commands and their completions are needed.
for brew in /opt/homebrew/bin/brew /usr/local/bin/brew /home/linuxbrew/.linuxbrew/bin/brew
    test -x "$brew"; or continue
    "$brew" shellenv fish | source
    break
end

set --local go_path "$HOME/go"
set --query GOPATH; and set go_path "$GOPATH"
set --global --export PIP_REQUIRE_VIRTUALENV true

fish_add_path --path "$HOME/.local/bin"
fish_add_path --path "$HOME/.docker/bin"
fish_add_path --path "$go_path/bin"
fish_add_path --path "/snap/bin"

# =============================================================================
# MARK: Interactive configuration
# =============================================================================
status is-interactive; or return

# Set visual and editor to Zed.
set --global --export VISUAL "zed --wait ."
set --global --export EDITOR "zed --wait ."

# Use Fish's native suggestions, highlighting, history, and completion menu.
set --global fish_greeting

# Preview files with bat and directories with eza during fuzzy searches.
set -Ux fifc_editor "zed --wait ."
set --global fzf_preview_dir_cmd eza --all --group-directories-first --color=always
set --global --export FZF_DEFAULT_OPTS '\
    --height=100% \
    --bind=alt-p:toggle-preview \
    --bind=alt-w:toggle-preview-wrap \
    --preview-window=bottom'

if functions --query fzf_configure_bindings
    fzf_configure_bindings --directory=ctrl-t
end

# Keep the shared Starship prompt.
starship init fish | source

# 1Password Plugins ───────────────────────────────────────────────────────────

# Authenticate GitHub CLI commands through the configured 1Password plugin.
# https://github.com/1Password/shell-plugins#managing-shell-plugins-in-your-own-dotfiles
function gh --wraps gh -d '1Password shell plugin for GitHub CLI'
    op plugin run -- gh $argv
end

set --global --export OP_PLUGIN_ALIASES_SOURCED 1

# =============================================================================
# MARK: Infrastructure
# =============================================================================

# Load functions and aliases.
source "$__fish_config_dir/aliases.fish"

# Load machine-specific extras.
if test -f "$__fish_config_dir/config.mc.fish"
    source "$__fish_config_dir/config.mc.fish"
end
