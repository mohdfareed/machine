#!/usr/bin/env python3
"""Quick test of our enhanced utilities."""

import sys
from pathlib import Path

# Add app_new to path
sys.path.insert(0, str(Path(__file__).parent / "app_new"))

from utils import (
    create_temp_dir,
    create_temp_file,
    get_platform,
    load_env_vars,
    logger,
    recursive_link,
    run_shell_command,
)


def test_utilities():
    """Test our enhanced utilities."""
    logger.info("Testing enhanced utilities...")

    # Test platform detection
    platform = get_platform()
    logger.info(f"Detected platform: {platform}")

    # Test temp file creation
    temp_dir = create_temp_dir()
    logger.info(f"Created temp directory: {temp_dir}")

    temp_file = create_temp_file(".txt")
    temp_file.write_text("Hello, world!")
    logger.info(f"Created temp file: {temp_file}")

    # Test shell command
    try:
        result = run_shell_command(
            ["echo", "Hello from shell"], capture_output=True
        )
        logger.info(f"Shell command result: {result}")
    except Exception as e:
        logger.error(f"Shell command failed: {e}")

    # Test environment loading (with a mock env file)
    mock_env_file = create_temp_file(".sh")
    mock_env_file.write_text(
        """
export TEST_VAR="test_value"
export ANOTHER_VAR="another_value"
"""
    )

    try:
        env_vars = load_env_vars(mock_env_file)
        logger.info(f"Loaded environment variables: {list(env_vars.keys())}")
    except Exception as e:
        logger.error(f"Environment loading failed: {e}")

    logger.info("✓ All utility tests completed")


if __name__ == "__main__":
    test_utilities()
