# =============================================================================
# MARK: Infrastructure
# =============================================================================

# Load public variables prepared by deployment.
if test -f "$__fish_config_dir/mc/env.fish"
    source "$__fish_config_dir/mc/env.fish"
end

# =============================================================================
# MARK: Environment
# =============================================================================

# Activate Homebrew (arm mac and wsl).
for brew in /opt/homebrew/bin/brew /home/linuxbrew/.linuxbrew/bin/brew
    test -x "$brew"; or continue
    "$brew" shellenv fish | source
    break
end

set --global --export PIP_REQUIRE_VIRTUALENV true
set --global --export GOPATH "$HOME/.go"

fish_add_path --path "$HOME/.local/bin"
fish_add_path --path "$HOME/.docker/bin"
fish_add_path --path "$GOPATH/bin"

# =============================================================================
# MARK: Interactive configuration
# =============================================================================
status is-interactive; or return

set --global fish_greeting
set --global --export fifc_editor zed

# Preview files with bat and directories with eza during fuzzy searches.
set --global fifc_eza_opts --all --color=always --icons --git --group-directories-first
set --global fzf_preview_dir_cmd eza --all --color=always --icons --git --group-directories-first
if functions --query fzf_configure_bindings
    fzf_configure_bindings --directory=ctrl-t
end

# Keep the shared Starship prompt.
starship init fish | source

# =============================================================================
# MARK: Infrastructure
# =============================================================================

# Load functions and aliases.
source "$__fish_config_dir/aliases.fish"

# Load machine-specific extras.
if test -f "$__fish_config_dir/config.mc.fish"
    source "$__fish_config_dir/config.mc.fish"
end
