"""Install the Wake PC user LaunchAgent from this reviewed checkout on macOS."""

import os
import plistlib
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Write the user agent and restart only the Wake PC helper."""
    if sys.platform != "darwin":
        raise SystemExit("Wake PC helper deployment requires macOS")

    directory = Path(__file__).resolve().parent
    interpreter = Path("/opt/homebrew/bin/python3")
    if not interpreter.is_file() or not Path("/opt/homebrew/bin/wakeonlan").is_file():
        raise FileNotFoundError("Existing Homebrew python3 and wakeonlan are required")
    label = "local.homepage.wake-pc"
    target = Path.home() / "Library/LaunchAgents" / f"{label}.plist"
    domain = f"gui/{os.getuid()}"
    log = str(Path.home() / "Library/Logs/homepage-wake-pc.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Keep paths tied to the deployed checkout, not a second copy of the helper.
    target.write_bytes(
        plistlib.dumps(
            {
                "Label": label,
                "ProgramArguments": [
                    str(interpreter),
                    str(directory / "wake_pc.py"),
                    str(directory / "settings.json"),
                ],
                "RunAtLoad": True,
                "KeepAlive": True,
                "ThrottleInterval": 30,
                "StandardOutPath": log,
                "StandardErrorPath": log,
            }
        )
    )
    loaded = subprocess.run(
        ["launchctl", "print", f"{domain}/{label}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if loaded.returncode == 0:
        subprocess.run(["launchctl", "bootout", f"{domain}/{label}"], check=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(target)], check=True)
    subprocess.run(
        [
            "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
            "serve",
            "--bg",
            "--set-path=/actions/wake-pc",
            "http://127.0.0.1:8766/actions/wake-pc",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
