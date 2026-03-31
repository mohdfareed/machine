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


def chatmock_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.5):
            return True
    except OSError:
        return False


if chatmock_running():
    print("ChatMock is already running at http://127.0.0.1:8000/v1")
    print("If this is the first run, complete `chatmock login` in a terminal first.")
    raise SystemExit

if sys.platform.startswith("win"):
    runners = [
        [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-Command",
            "Start-Process -WindowStyle Hidden chatmock -ArgumentList 'serve'",
        ],
        [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-Command",
            (
                "Start-Process -WindowStyle Hidden uv "
                "-ArgumentList 'tool','run','--from','chatmock','chatmock','serve'"
            ),
        ],
    ]
else:
    shell = os.environ.get("SHELL", "/bin/sh")
    runners = [
        [shell, "-lc", "nohup chatmock serve >/dev/null 2>&1 &"],
        [shell, "-lc", "nohup uv tool run --from chatmock chatmock serve >/dev/null 2>&1 &"],
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
        print("Started ChatMock at http://127.0.0.1:8000/v1")
        print("If this is the first run, complete `chatmock login` in a terminal first.")
        raise SystemExit
    time.sleep(0.25)

raise SystemExit("ChatMock did not start. Run `chatmock login` in a terminal, then try again.")
