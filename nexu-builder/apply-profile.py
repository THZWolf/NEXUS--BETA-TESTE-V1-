#!/usr/bin/env python3
"""Validate a locally authored installer profile and write its runtime settings."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ALLOWED_PACKAGES = {
    "nexus-server",
    "nexus-avatar",
    "lynis",
    "yara",
    "wireshark",
    "tcpdump",
    "clamav",
    "open-jarvis",
    "open-eye",
}
ALLOWED_THEMES = {"cyan", "violet", "amber"}


def apply_profile(profile_path: Path, destination: Path) -> int:
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid build profile: {exc}", file=sys.stderr)
        return 1
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        print("Unsupported build profile schema.", file=sys.stderr)
        return 1

    packages = profile.get("packages")
    theme = profile.get("theme")
    icon = profile.get("icon")
    personality = profile.get("personality")
    if (
        not isinstance(packages, list)
        or any(not isinstance(item, str) or item not in ALLOWED_PACKAGES for item in packages)
        or not isinstance(theme, str)
        or theme not in ALLOWED_THEMES
        or not isinstance(icon, str)
        or icon != "dragon-mage"
        or not isinstance(personality, dict)
    ):
        print("Build profile contains unsupported package or visual settings.", file=sys.stderr)
        return 1

    name = personality.get("name")
    tone = personality.get("tone")
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 64
        or re.search(r"[\x00-\x1f<>]", name)
        or not isinstance(tone, str)
        or not 1 <= len(tone) <= 128
        or re.search(r"[\x00-\x1f<>]", tone)
    ):
        print("Invalid avatar name or tone.", file=sys.stderr)
        return 1

    destination.mkdir(parents=True, exist_ok=True)
    runtime = {
        "name": name,
        "language": "pt-BR",
        "tone": tone,
        "theme": theme,
        "icon": icon,
        "avatar": {"enabled": True, "motion": "subtle"},
    }
    (destination / "personality.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "build-profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: apply-profile.py PROFILE.json DESTINATION_DIR", file=sys.stderr)
        return 2
    return apply_profile(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    raise SystemExit(main())
