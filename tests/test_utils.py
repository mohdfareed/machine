"""Utilities module tests."""

import logging
import shutil
from pathlib import Path
from typing import Any, Generator, Literal
from unittest.mock import patch

import pytest

from app import utils
from app.utils import Shell, create_temp_dir, create_temp_file, link, load_env_vars
from app.utils.logging import StripMarkupFilter


@pytest.fixture(name="temp_dir")
def temp_dir_fixture() -> Generator[Path, Any, None]:
    """Create a temporary directory fixture for file-related tests."""
    path = Path("temp_test_dir")
    path.mkdir(exist_ok=True)

    yield path
    shutil.rmtree(path)


@pytest.fixture(name="temp_file")
def temp_file_fixture(temp_dir: Path) -> Generator[Any, Any, None]:
    """Create a temporary file fixture for file-related tests."""
    file_path = temp_dir / "temp_test_file.txt"
    file_path.touch(exist_ok=True)

    yield file_path
    file_path.unlink()


def test_strip_markup_filter() -> None:
    """Test the StripMarkupFilter class."""
    log_record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="[bold]Bold message[/bold]",
        args=(),
        exc_info=None,
    )
    filter_instance = StripMarkupFilter()

    assert filter_instance.filter(log_record) is True
    assert log_record.msg == "Bold message"


def test_link(temp_dir: Path) -> None:
    """Test the link function."""
    directory = temp_dir  # Use a local variable to avoid name conflict with the fixture
    source = directory / "source_file.txt"
    source.touch()  # This will create an actual file to use as the source
    target = directory / "target_file.txt"

    link(source, target)

    assert target.is_symlink()
    assert target.readlink() == source


def test_create_temp_dir() -> None:
    """Test the create_temp_dir function."""
    with patch("atexit.register") as mock_register:
        file = create_temp_dir()

        assert file.exists()
        assert file.is_dir()

        mock_register.assert_called_once()
        shutil.rmtree(file)


def test_create_temp_dir_cleanup() -> None:
    """Test the create_temp_dir function cleanup."""
    temp_dir = create_temp_dir()
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    shutil.rmtree(temp_dir)
    assert not temp_dir.exists()


def test_create_temp_file() -> None:
    """Test the create_temp_file function."""
    with patch("atexit.register") as mock_register:
        file = create_temp_file("test")
        file.touch()

        assert file.exists()
        assert file.is_file()

        mock_register.assert_called_once()
        file.unlink()


def test_create_temp_file_cleanup() -> None:
    """Test the create_temp_file function cleanup."""
    temp_file = create_temp_file()
    temp_file.touch()
    assert temp_file.exists()
    assert temp_file.is_file()
    temp_file.unlink()
    assert not temp_file.exists()


def test_shell() -> None:
    """Test the shell function."""

    shell = Shell()
    shell.execute("echo 'sudo test'")
    shell.execute("echo 'error test'")
    shell.execute("echo 'warning test'")
    shell.execute("echo 'info test'", info=True)
    shell.execute("echo")


def test_shell_execute_with_info() -> None:
    """Test the shell execute function with info logging."""
    shell = Shell()
    result = shell.execute("echo 'info test'", info=True)
    assert result.returncode == 0
    assert "info test" in result.output


def test_shell_execute_with_error() -> None:
    """Test the shell execute function with error logging."""
    shell = Shell()
    result = shell.execute("echo 'error test'", throws=False)
    assert result.returncode == 0
    assert "error test" in result.output


def test_env(temp_file: Path) -> None:
    """Test loading env vars from a file."""

    temp_file.write_text(
        """
        export TEST_ENV_VAR="test"
        """.strip()
    )

    env_vars = load_env_vars(temp_file)
    assert env_vars["TEST_ENV_VAR"] == "test"


def test_with_status_decorator() -> None:
    """Test the with_status decorator."""

    @utils.with_status("Testing status")
    def sample_function() -> Literal["Success"]:
        return "Success"

    result = sample_function()
    assert result == "Success"


def test_with_progress_decorator() -> None:
    """Test the with_progress decorator."""

    @utils.with_progress("Testing progress")
    def sample_function(items: list[Any]) -> Any:
        return items

    sample_function([1, 2, 3])
