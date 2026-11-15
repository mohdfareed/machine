"""Configure the Wake PC helper under Homebrew's Supervisor service."""

import json
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from string import Template


def main() -> None:
    """Update only the wake helper and its private Tailscale Serve route."""
    if sys.platform != "darwin":
        raise SystemExit("Wake PC helper deployment requires macOS")

    # =========================================================================
    # MARK: Write the Supervisor Configuration
    # =========================================================================

    directory = Path(__file__).resolve().parent
    settings = json.loads((directory / "settings.json").read_text())
    waitress = shutil.which("waitress-serve")
    supervisorctl = shutil.which("supervisorctl")
    if not waitress or not supervisorctl or not Path("/opt/homebrew/bin/wakeonlan").is_file():
        raise FileNotFoundError("Run mc deploy -m homelab to install the helper's packages")

    target = Path("/opt/homebrew/etc/supervisor.d/wake-pc.ini")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        Template((directory / "supervisor.ini").read_text()).substitute(
            directory=directory,
            waitress=shlex.quote(waitress),
            port=settings["port"],
            timeout=settings["timeout_seconds"],
        )
    )

    # =========================================================================
    # MARK: Start Supervisor and Reload the Helper
    # =========================================================================

    subprocess.run(["brew", "services", "start", "supervisor"], check=True)
    control = [supervisorctl, "-c", "/opt/homebrew/etc/supervisord.conf"]

    # Homebrew starts the daemon asynchronously; wait briefly for its control socket.
    for _ in range(20):
        ready = subprocess.run(
            [*control, "pid"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
        )
        if ready.returncode == 0:
            break
        time.sleep(0.25)

    subprocess.run([*control, "update", "wake-pc"], check=True)
    subprocess.run([*control, "restart", "wake-pc"], check=True)

    # =========================================================================
    # MARK: Configure the Private Serve Route
    # =========================================================================

    subprocess.run(
        [
            "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
            "serve",
            "--bg",
            "--set-path=/actions/wake-pc",
            f"http://127.0.0.1:{settings['port']}/actions/wake-pc",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
