"""Prepare service-account authentication without the desktop app."""

import getpass
import os
import sys
import warnings
from pathlib import Path

# =============================================================================
# MARK: Prepare authentication
# =============================================================================


def deployment_environment() -> dict[str, str]:
    """Return a process environment authenticated with the saved service-account token."""

    # Reuse the saved token with owner-only permissions.
    path = Path.home() / ".config" / "machine" / "credentials" / "1password-token"
    environment = os.environ.copy()

    # Connect credentials take precedence over service-account authentication.
    environment.pop("OP_CONNECT_HOST", None)
    environment.pop("OP_CONNECT_TOKEN", None)

    token = ""
    if path.exists():
        path.chmod(0o600)
        token = path.read_text().strip()
    if token:
        environment["OP_SERVICE_ACCOUNT_TOKEN"] = token
        return environment

    environment["OP_SERVICE_ACCOUNT_TOKEN"] = _prompt_token()
    return environment


def replace_token(environment: dict[str, str]) -> None:
    """Offer a private replacement after a secret-loading failure."""

    if not sys.stdin.isatty():
        raise RuntimeError(
            "1Password loading failed; run mc deploy in a terminal to replace the token"
        )
    if input("Enter a replacement service-account token? [y/N] ").strip().lower() != "y":
        raise RuntimeError("Deployment stopped; saved token unchanged")
    environment["OP_SERVICE_ACCOUNT_TOKEN"] = _prompt_token()


def _prompt_token() -> str:
    # Require a terminal and fail rather than fall back to echoing the token.
    if not sys.stdin.isatty():
        raise RuntimeError("Run mc deploy in a terminal to enter a 1Password service-account token")
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        token = getpass.getpass("1Password service-account token (hidden): ").strip()
    if not token:
        raise ValueError("No token entered")

    # Leave the saved credential untouched until a nonempty replacement is entered.
    path = Path.home() / ".config" / "machine" / "credentials" / "1password-token"
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(token)
    return token
