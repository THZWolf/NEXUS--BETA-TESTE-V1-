#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
    echo "Usage: test-iso-qemu.sh PATH_TO_ISO" >&2
    exit 2
fi
if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
    echo "qemu-system-x86_64 is required." >&2
    exit 1
fi

iso=$(CDPATH= cd -- "$(dirname -- "$1")" && pwd)/$(basename -- "$1")
memory=${NEXU_QEMU_MEMORY:-4096}
cpus=${NEXU_QEMU_CPUS:-2}
if [ -e /dev/kvm ]; then
    exec qemu-system-x86_64 -enable-kvm -m "$memory" -smp "$cpus" \
        -cdrom "$iso" -boot order=d
fi
exec qemu-system-x86_64 -accel tcg -m "$memory" -smp "$cpus" \
    -cdrom "$iso" -boot order=d
