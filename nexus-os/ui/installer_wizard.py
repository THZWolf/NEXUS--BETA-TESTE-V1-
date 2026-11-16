"""Small interactive build-profile wizard with safe, local-only defaults."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

PROFILES = {
    "standard": ["nexus-server", "nexus-avatar"],
    "kali-defensive": ["lynis", "yara", "wireshark", "tcpdump", "clamav"],
    "jarvis": ["open-jarvis"],
    "goodeye": ["open-eye"],
}
THEMES = {"cyan", "violet", "amber"}


def ask(prompt: str, default: str) -> str:
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def choose_theme() -> str:
    while True:
        theme = ask("Tema (cyan/violet/amber)", "cyan").lower()
        if theme in THEMES:
            return theme
        print("Tema inválido; escolha cyan, violet ou amber.")


def build_profile() -> dict[str, object]:
    print("NEXU-OS · configuração local da build")
    print("Perfis: standard, kali-defensive (somente ferramentas defensivas), jarvis, goodeye")
    selected = ask("Perfis separados por vírgula", "standard").split(",")
    names = [entry.strip().lower() for entry in selected if entry.strip()]
    unknown = sorted(set(names) - PROFILES.keys())
    if unknown:
        raise ValueError(f"Perfis desconhecidos: {', '.join(unknown)}")
    packages = sorted({package for name in names for package in PROFILES[name]})
    return {
        "schema_version": 1,
        "packages": packages,
        "theme": choose_theme(),
        "icon": "dragon-mage",
        "personality": {
            "name": ask("Nome do avatar", "Nexus")[:64],
            "language": "pt-BR",
            "tone": ask("Tom de voz", "claro, respeitoso e objetivo")[:128],
        },
    }


def save_profile(profile: dict[str, object], output: Path) -> None:
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as temporary:
        json.dump(profile, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temp_path = Path(temporary.name)
    temp_path.chmod(0o600)
    temp_path.replace(output)


def main() -> int:
    output = Path(
        os.environ.get(
            "NEXUS_PROFILE_OUTPUT",
            Path.home() / ".config/nexus-os/build-profile.json",
        )
    )
    try:
        profile = build_profile()
        save_profile(profile, output)
    except (OSError, ValueError) as exc:
        print(f"Erro ao salvar perfil: {exc}", file=sys.stderr)
        return 1
    print(f"Perfil salvo em {output}")
    print("A seleção é declarativa; pacotes só são instalados pelo processo de build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
