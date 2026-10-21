"""Owner-authenticated Wake PC action behind the Mac's private Tailscale Serve."""

import json
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import cast


class _Server(HTTPServer):
    config: dict[str, str]
    last_attempt = float("-inf")


class _Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def _reply(self, status, message):
        body = json.dumps({"message": message}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.send_header("Vary", "Origin")
        if self.headers.get("Origin") == cast(_Server, self.server).config["origin"]:
            self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
            self.send_header("Access-Control-Allow-Methods", "POST")
            self.send_header("Access-Control-Allow-Headers", "X-Wake-PC")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _authorized(self):
        config = cast(_Server, self.server).config
        # Serve replaces this header with the authenticated peer's identity.
        # Loopback processes are trusted; never expose this backend on the LAN.
        if (
            self.client_address[0] != "127.0.0.1"
            or self.headers.get_all("Tailscale-User-Login") != [config["login"]]
            or self.headers.get("Host") != config["host"]
            or self.headers.get("Origin") != config["origin"]
        ):
            self._reply(403, "Owner identity and dashboard origin required")
            return False
        if self.path != "/actions/wake-pc":
            self._reply(404, "Unknown action")
            return False
        return True

    def do_OPTIONS(self):
        if not self._authorized():
            return
        if (
            self.headers.get("Access-Control-Request-Method") != "POST"
            or self.headers.get("Access-Control-Request-Headers", "").lower() != "x-wake-pc"
        ):
            self._reply(403, "Unsupported preflight")
            return
        self._reply(200, "POST permitted")

    def do_POST(self):
        if not self._authorized():
            return
        if self.headers.get("X-Wake-PC") != "1":
            self._reply(403, "Dashboard action header required")
            return
        if self.headers.get("Content-Length", "0") != "0" or "Transfer-Encoding" in self.headers:
            self._reply(400, "Empty body required")
            return
        server = cast(_Server, self.server)
        if time.monotonic() - server.last_attempt < 5:
            self._reply(429, "Wait five seconds before retrying")
            return
        server.last_attempt = time.monotonic()
        try:
            result = subprocess.run(
                ["/opt/homebrew/bin/wakeonlan", "BC-FC-E7-D6-D0-9D", "D8-B3-2F-69-8D-09"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as error:
            print(f"Wake command failed: {error}", flush=True)
            self._reply(502, "Wake command failed; check helper log")
            return
        print(result.stdout.strip(), flush=True)
        self._reply(200, "Wake command completed; PC awake status not confirmed")


def main():
    """Start the fixed action on loopback, reachable through Tailscale Serve."""
    config = json.loads(Path(sys.argv[1]).read_text())
    with _Server(("127.0.0.1", 8766), _Handler) as server:
        server.config = config
        server.serve_forever()


if __name__ == "__main__":
    main()
