"""Mock weather HTTP server for Day 10 MCP + Agent Applications Lab.

Run:
  python weather_server/mock_weather_server.py

Then open:
  http://localhost:60004/current_temperature
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class WeatherHandler(BaseHTTPRequestHandler):
    temperature_c = 31.0
    condition = "Cloudy"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlparse(self.path).path
        if path == "/current_temperature":
            self._send_json(
                {
                    "location": "Singapore",
                    "temperature_c": self.temperature_c,
                    "condition": self.condition,
                    "source": "mock classroom HTTP server",
                }
            )
        elif path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": True, "message": "Unknown endpoint"}, status=404)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[weather-server] {self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="Bind address. Use 0.0.0.0 for instructor-hosted mode.")
    parser.add_argument("--port", type=int, default=60004)
    parser.add_argument("--temperature", type=float, default=31.0)
    parser.add_argument("--condition", default="Cloudy")
    args = parser.parse_args()

    WeatherHandler.temperature_c = args.temperature
    WeatherHandler.condition = args.condition

    server = ThreadingHTTPServer((args.host, args.port), WeatherHandler)
    print(f"Mock weather server running at http://{args.host}:{args.port}/current_temperature")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock weather server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
