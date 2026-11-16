#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
    echo "Usage: test-iso-headless.sh PATH_TO_ISO" >&2
    exit 2
fi
iso=$(CDPATH= cd -- "$(dirname -- "$1")" && pwd)/$(basename -- "$1")
if ! command -v qemu-system-x86_64 >/dev/null 2>&1 || ! command -v timeout >/dev/null 2>&1; then
    echo "qemu-system-x86_64 and timeout are required." >&2
    exit 1
fi

log=$(mktemp "${TMPDIR:-/tmp}/nexu-qemu-serial.XXXXXX")
trap 'rm -f "$log"' EXIT HUP INT TERM
set +e
timeout --signal=TERM --kill-after=10s 240s \
    qemu-system-x86_64 \
    -machine q35 -accel tcg -m 4096 -smp 2 \
    -cdrom "$iso" -boot order=d -display none \
    -serial "file:$log" -monitor none -no-reboot
qemu_status=$?
set -e

cat "$log"
if [ "$qemu_status" -ne 124 ] && [ "$qemu_status" -ne 137 ] && [ "$qemu_status" -ne 0 ]; then
    echo "QEMU failed with exit status $qemu_status." >&2
    exit "$qemu_status"
fi
if ! grep -q 'NEXU_STATUS: boot' "$log"; then
    echo "The ISO did not report the expected boot status over serial." >&2
    exit 1
fi
echo "Headless ISO boot status verified."
