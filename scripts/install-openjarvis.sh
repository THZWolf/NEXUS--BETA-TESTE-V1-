#!/bin/sh
set -eu

printf '%s\n' \
  'OpenJarvis setup downloads the official Linux installer and a starter model.' \
  'It configures the chat-simple preset without agent tools; model downloads may use several gigabytes.'
printf 'Continue? [y/N] '
read -r answer
case "$answer" in
  y|Y|yes|YES) ;;
  *) echo 'Cancelled.'; exit 0 ;;
esac

installer=$(mktemp)
trap 'rm -f "$installer"' EXIT HUP INT TERM
curl -fsSL https://open-jarvis.github.io/OpenJarvis/install.sh -o "$installer"
bash "$installer"
if ! command -v jarvis >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/jarvis" ]; then
    PATH="$HOME/.local/bin:$PATH"
    export PATH
  fi
fi
if ! command -v jarvis >/dev/null 2>&1; then
  echo 'OpenJarvis installation completed but the jarvis command is unavailable.' >&2
  exit 1
fi
jarvis init --preset chat-simple
