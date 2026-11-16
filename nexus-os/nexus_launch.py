#!/usr/bin/env python3
"""Boot-time coordinator for the local Nexus services."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import webbrowser
from urllib.error import URLError
from urllib.request import urlopen

SERVICES = ("nexus-server.service", "nexus-avatar.service")


def wait_for_endpoint(url: str, timeout: float = 15) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except (OSError, URLError):
            time.sleep(0.25)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-open", action="store_true", help="Do not open the local avatar UI.")
    args = parser.parse_args()

    if shutil.which("systemctl") is None:
        print("systemctl is required to start Nexus services.", file=sys.stderr)
        return 1

    for service in SERVICES:
        result = subprocess.run(
            ["systemctl", "start", service],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip()
            print(f"Failed to start {service}: {detail}", file=sys.stderr)
            return result.returncode

    if not args.no_open:
        if not wait_for_endpoint("http://127.0.0.1:8765/health") or not wait_for_endpoint(
            "http://127.0.0.1:8766/health"
        ):
            print("NEXU-OS local services did not become healthy.", file=sys.stderr)
            return 1
        if not webbrowser.open("http://127.0.0.1:8766/"):
            print("Could not open a browser; visit http://127.0.0.1:8766/ manually.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
