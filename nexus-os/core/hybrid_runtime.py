"""A constrained bridge for launching administrator-approved Windows applications."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class HybridRuntimeError(RuntimeError):
    """Raised when a configured hybrid-runtime operation cannot be completed."""


def _is_wsl() -> bool:
    release = Path("/proc/sys/kernel/osrelease")
    try:
        return "microsoft" in release.read_text(encoding="utf-8").lower()
    except OSError:
        return False


class HybridRuntime:
    """Expose Linux/WSL capabilities without accepting arbitrary command lines."""

    def __init__(self, allowlist_path: Path | None = None) -> None:
        self.allowlist_path = allowlist_path or Path(
            os.environ.get(
                "NEXUS_WIN32_ALLOWLIST",
                "/etc/nexus-os/win32-apps.json",
            )
        )

    def capabilities(self) -> dict[str, Any]:
        windows_interop = _is_wsl()
        return {
            "linux": True,
            "wsl": windows_interop,
            "windows_interop": bool(windows_interop and shutil.which("cmd.exe")),
        }

    def launch_windows_app(self, app_name: str) -> subprocess.Popen[bytes]:
        """Launch a named, preconfigured executable without arguments or a shell."""
        if not _is_wsl():
            raise HybridRuntimeError("Win32 interop is available only inside WSL.")
        if not shutil.which("cmd.exe"):
            raise HybridRuntimeError("WSL Win32 interop is unavailable or disabled.")
        if not app_name or len(app_name) > 64:
            raise HybridRuntimeError("Invalid application name.")

        try:
            allowlist = json.loads(self.allowlist_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HybridRuntimeError(f"Cannot read Win32 allowlist: {exc}") from exc
        if not isinstance(allowlist, dict):
            raise HybridRuntimeError("Win32 allowlist must be a JSON object.")

        executable = allowlist.get(app_name)
        if (
            not isinstance(executable, str)
            or not re.fullmatch(r"/mnt/[a-zA-Z]/[a-zA-Z0-9 _./()-]+\.exe", executable)
        ):
            raise HybridRuntimeError(f"Application is not approved: {app_name}")

        # A fixed executable and no caller-provided arguments prevent this bridge
        # from becoming a general-purpose command execution endpoint.
        return subprocess.Popen(
            [executable],
            shell=False,
            close_fds=True,
        )
