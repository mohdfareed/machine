"""Owner-only Wake PC action behind native Tailscale Serve."""

import json
import subprocess
import time
from pathlib import Path

from flask import Flask, Response, request

# =============================================================================
# MARK: Configure the Action
# =============================================================================

app = Flask(__name__)
_settings = json.loads(Path(__file__).with_name("settings.json").read_text())
_last_attempt = float("-inf")


# =============================================================================
# MARK: Wake the PC
# =============================================================================


@app.post("/actions/wake-pc")
def wake_pc():
    """Run the configured wake command, without claiming the PC is awake."""
    global _last_attempt

    # Require an explicit, empty action request from either client.
    if request.headers.get("X-Wake-PC") != "1":
        return {"message": "Wake action header required"}, 403
    if request.content_length not in (None, 0) or "Transfer-Encoding" in request.headers:
        return {"message": "Empty body required"}, 400
    if time.monotonic() - _last_attempt < _settings["cooldown_seconds"]:
        return {"message": "Wait before retrying"}, 429

    # Waitress uses one worker; failed attempts also consume the cooldown.
    _last_attempt = time.monotonic()
    addresses = [interface["mac"] for interface in _settings["interfaces"].values()]
    try:
        subprocess.run(
            ["/opt/homebrew/bin/wakeonlan", *addresses],
            check=True,
            capture_output=True,
            timeout=_settings["timeout_seconds"],
        )
    except OSError, subprocess.SubprocessError:
        app.logger.exception("Wake command failed")
        return {"message": "Wake command failed; check helper log"}, 502

    return {"message": "Wake sent; PC awake status not confirmed"}


# =============================================================================
# MARK: Restrict Access
# =============================================================================


@app.before_request
def _authorize():
    # Native Serve supplies identity. Loopback processes remain trusted.
    if (
        request.remote_addr != "127.0.0.1"
        or request.headers.getlist("Tailscale-User-Login") != [_settings["login"]]
        or request.host != _settings["host"]
        or request.headers.get("Origin") != _settings["origin"]
    ):
        return {"message": "Owner identity and dashboard origin required"}, 403


@app.after_request
def _cors(response: Response) -> Response:
    response.headers.update(
        {
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": _settings["origin"],
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "X-Wake-PC",
        }
    )
    return response
