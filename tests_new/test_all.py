"""Tests for the new machine setup tool."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app_new import files, machine, packages, private, utils


class TestMachineDetection:
    """Test machine detection and configuration loading."""

    def test_detect_machine_from_env(self):
        """Test machine detection from environment variable."""
        with patch.dict(os.environ, {"MACHINE": "test-machine"}):
            result = machine.detect_current_machine()
            assert result == "test-machine"

    def test_detect_machine_no_env(self):
        """Test machine detection when no env variable set."""
        with patch.dict(os.environ, {}, clear=True):
            result = machine.detect_current_machine()
            assert result is None

    def test_load_machine_config_existing(self, tmp_path):
        """Test loading configuration for existing machine."""
        # Create test directory structure
        config_dir = tmp_path / "config"
        machine_dir = config_dir / "test-machine"
        base_dir = config_dir / "base"

        machine_dir.mkdir(parents=True)
        base_dir.mkdir(parents=True)

        with patch("app_new.machine.Path") as mock_path:
            mock_path.return_value.parent.parent = config_dir

            config = machine.load_machine_config("test-machine")
            assert config is not None
            assert config.id == "test-machine"

    def test_load_machine_config_nonexistent(self, tmp_path):
        """Test loading configuration for non-existent machine."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        with patch("app_new.machine.Path") as mock_path:
            mock_path.return_value.parent.parent = config_dir

            config = machine.load_machine_config("nonexistent")
            assert config is None


class TestPackageManagement:
    """Test package file parsing and installation."""

    def test_parse_combined_package_file(self, tmp_path):
        """Test parsing a combined package file like apt.pkg."""
        package_file = tmp_path / "test.pkg"
        package_file.write_text(
            """
# Test package file
apt git vim
apt python3

snap docker
snap --classic code

brew git
brew tmux

winget Git.Git
"""
        )

        result = packages.parse_combined_package_file(package_file)

        assert "apt" in result
        assert "git" in result["apt"]
        assert "vim" in result["apt"]
        assert "python3" in result["apt"]

        assert "snap" in result
        assert "docker" in result["snap"]

        assert "snap_classic" in result
        assert "code" in result["snap_classic"]

        assert "brew" in result
        assert "git" in result["brew"]
        assert "tmux" in result["brew"]

        assert "winget" in result
        assert "Git.Git" in result["winget"]

    def test_find_package_files(self, tmp_path):
        """Test finding package files in directory."""
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        # Create test files
        (packages_dir / "test.pkg").touch()
        (packages_dir / "brewfile").touch()
        (packages_dir / "requirements.txt").touch()
        (packages_dir / "not-a-package.txt").touch()

        result = packages.find_package_files(packages_dir)

        filenames = [f.name for f in result]
        assert "test.pkg" in filenames
        assert "brewfile" in filenames
        assert "requirements.txt" in filenames


class TestFileHandling:
    """Test configuration file linking."""

    def test_find_config_files(self, tmp_path):
        """Test finding config files in directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create test files
        (config_dir / "gitconfig").touch()
        (config_dir / "zshrc").touch()
        (config_dir / ".DS_Store").touch()  # Should be filtered out
        (config_dir / "subdir").mkdir()  # Should be ignored

        result = files.find_config_files(config_dir)

        filenames = [f.name for f in result]
        assert "gitconfig" in filenames
        assert "zshrc" in filenames
        assert ".DS_Store" not in filenames
        assert len(result) == 2

    def test_config_targets_mapping(self):
        """Test that config target mapping works."""
        targets = files.get_config_targets()

        assert "zshrc" in targets
        assert "gitconfig" in targets
        assert ".gitconfig" in targets
        assert targets["zshrc"].name == ".zshrc"


class TestPrivateFiles:
    """Test private files handling."""

    def test_find_ssh_keys(self, tmp_path):
        """Test finding SSH keys in directory."""
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()

        # Create test SSH keys
        (keys_dir / "github").touch()  # Private key
        (keys_dir / "github.pub").touch()  # Public key
        (keys_dir / "personal.key").touch()  # Private key with .key extension
        (keys_dir / "personal.key.pub").touch()  # Public key
        (keys_dir / "config").touch()  # Not a key

        result = private.find_ssh_keys(keys_dir)

        key_names = [k.name for k in result]
        assert "github" in key_names
        assert "personal.key" in key_names
        assert "github.pub" not in key_names
        assert "personal.key.pub" not in key_names
        assert "config" not in key_names


class TestUtils:
    """Test utility functions."""

    @patch("subprocess.run")
    def test_run_shell_command_success(self, mock_run):
        """Test successful shell command execution."""
        mock_run.return_value.returncode = 0

        utils.run_shell_command(["echo", "test"])

        mock_run.assert_called_once_with(
            ["echo", "test"], cwd=None, check=True
        )

    @patch("subprocess.run")
    def test_run_shell_command_with_capture(self, mock_run):
        """Test shell command with output capture."""
        mock_run.return_value.stdout = "test output\n"

        result = utils.run_shell_command(["echo", "test"], capture_output=True)

        assert result == "test output"
        mock_run.assert_called_once_with(
            ["echo", "test"],
            cwd=None,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_create_symlink_dry_run(self, tmp_path, caplog):
        """Test symlink creation in dry run mode."""
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.touch()

        utils.create_symlink(source, target, dry_run=True)

        assert not target.exists()
        assert "[DRY RUN]" in caplog.text

    def test_create_symlink_real(self, tmp_path):
        """Test actual symlink creation."""
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_text("test content")

        utils.create_symlink(source, target, dry_run=False)

        assert target.is_symlink()
        assert target.read_text() == "test content"


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_setup_dry_run(self, tmp_path):
        """Test full setup process in dry run mode."""
        # Create test directory structure
        config_root = tmp_path / "config"
        base_dir = config_root / "base"
        machine_dir = config_root / "test-machine"
        packages_dir = machine_dir / "packages"

        base_dir.mkdir(parents=True)
        packages_dir.mkdir(parents=True)

        # Create test config files
        (base_dir / "gitconfig").write_text("[user]\n  name = Test")
        (base_dir / "zshrc").write_text("echo 'test'")

        # Create test package file
        (packages_dir / "test.pkg").write_text("apt git\nbrew tmux")

        # Mock the Path resolution
        with patch("app_new.machine.Path") as mock_path:
            mock_path.return_value.parent.parent = config_root

            config = machine.load_machine_config("test-machine")
            assert config is not None

            # Test file linking
            files.link_all_configs(config, dry_run=True)

            # Test package installation
            packages.install_all_packages(config, dry_run=True)


if __name__ == "__main__":
    pytest.main([__file__])
