#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Start ChatMock
# @raycast.mode fullOutput

import os
import socket
import subprocess
import sys
import time

from _machine import REPO_ROOT

# Optional parameters:
# @raycast.packageName Machine

BASE_URL = "http://127.0.0.1:8000/v1"
CHATMOCK_ARGS = "'serve','--enable-web-search'"
UV_ARGS = f"'tool','run','--from','chatmock','chatmock',{CHATMOCK_ARGS}"


def chatmock_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.5):
            return True
    except OSError:
        return False


def stop_existing_server() -> None:
    if sys.platform.startswith("win"):
        subprocess.run(
            [
                "pwsh",
                "-NoLogo",
                "-NoProfile",
                "-Command",
                (
                    "$ErrorActionPreference='SilentlyContinue'; "
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { $_.CommandLine -and $_.CommandLine -match 'chatmock' "
                    "-and $_.CommandLine -match 'serve' } | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        return

    shell = os.environ.get("SHELL", "/bin/sh")
    for command in (
        "pkill -f 'chatmock serve'",
        "pkill -f 'uv tool run --from chatmock chatmock serve'",
    ):
        subprocess.run(
            [shell, "-lc", command],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )


restarting = chatmock_running()
if restarting:
    stop_existing_server()
    for _ in range(20):
        if not chatmock_running():
            break
        time.sleep(0.25)
    else:
        raise SystemExit("Could not stop the existing ChatMock server.")

if sys.platform.startswith("win"):
    runners = [
        [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-Command",
            f"Start-Process -WindowStyle Hidden chatmock -ArgumentList {CHATMOCK_ARGS}",
        ],
        [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-Command",
            f"Start-Process -WindowStyle Hidden uv -ArgumentList {UV_ARGS}",
        ],
    ]
else:
    shell = os.environ.get("SHELL", "/bin/sh")
    runners = [
        [
            shell,
            "-lc",
            "nohup chatmock serve --reasoning-compat legacy --enable-web-search >/dev/null 2>&1 &",
        ],
        [
            shell,
            "-lc",
            (
                "nohup uv tool run --from chatmock chatmock serve "
                "--reasoning-compat legacy --enable-web-search >/dev/null 2>&1 &"
            ),
        ],
    ]

for runner in runners:
    proc = subprocess.run(
        runner,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode == 0:
        break
else:
    raise SystemExit("Could not start ChatMock. Ensure `chatmock` or `uv` is available.")

for _ in range(20):
    if chatmock_running():
        action = "Restarted" if restarting else "Started"
        raise SystemExit(f"{action} ChatMock at {BASE_URL}")
    time.sleep(0.25)

raise SystemExit("ChatMock did not start. Run `chatmock login` in a terminal, then try again.")
