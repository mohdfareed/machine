"""Machine configuration tests."""

from pathlib import Path

from app.config import ConfigFiles


def test_config_files():
    """Test configuration files."""

    config_files = ConfigFiles()
    config_path = Path(__file__).parent.parent / "config"

    assert config_files.vim == config_path / "vim"
    assert config_files.vscode == config_path / "vscode"
    assert config_files.gitconfig == config_path / ".gitconfig"
    assert config_files.gitignore == config_path / ".gitignore"
    assert config_files.ps_profile == config_path / "ps_profile.ps1"
    assert config_files.tmux == config_path / "tmux.conf"
    assert config_files.zed_settings == config_path / "zed_settings.jsonc"
    assert config_files.zshrc == config_path / "zshrc"
    assert config_files.zshenv == config_path / "zshenv"
