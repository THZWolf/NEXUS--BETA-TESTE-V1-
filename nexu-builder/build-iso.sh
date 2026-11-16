#!/bin/sh
set -eu

BUILDER_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$BUILDER_DIR/.." && pwd)
ISO_DIR="$PROJECT_ROOT/iso"
OVERLAY_DIR="$BUILDER_DIR/overlay"

if [ "$(id -u)" -ne 0 ]; then
    echo "ISO build requires root: sudo sh ./nexu-builder/build-iso.sh [--configure]" >&2
    exit 1
fi
if [ "$(dpkg --print-architecture)" != amd64 ]; then
    echo "Build the x86_64 ISO on a native amd64 Debian host." >&2
    exit 1
fi

configure=0
if [ "${1:-}" = "--configure" ]; then
    configure=1
    shift
fi
if [ "$#" -ne 0 ]; then
    echo "Usage: build-iso.sh [--configure]" >&2
    exit 2
fi

for command in lb mksquashfs unsquashfs sha256sum find install chmod cp python3; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Missing required command: $command" >&2
        exit 1
    fi
done

PROFILE_FILE=${NEXU_PROFILE_FILE:-/root/.config/nexus-os/build-profile.json}
if [ "$configure" -eq 1 ]; then
    NEXUS_PROFILE_OUTPUT="$PROFILE_FILE" \
        PYTHONPATH="$PROJECT_ROOT/nexus-os${PYTHONPATH:+:$PYTHONPATH}" \
        python3 -m ui.installer_wizard
fi

if [ -n "${NEXU_REAL_MKSQUASHFS:-}" ]; then
    REAL_MKSQUASHFS=$NEXU_REAL_MKSQUASHFS
else
    REAL_MKSQUASHFS=$(command -v mksquashfs)
fi
export NEXU_REAL_MKSQUASHFS="$REAL_MKSQUASHFS"
chmod 0755 "$BUILDER_DIR/bin/mksquashfs"
PATH="$BUILDER_DIR/bin:$PATH"
export PATH

mkdir -p "$ISO_DIR/config/includes.chroot" "$ISO_DIR/config/hooks/live"
cp -a "$OVERLAY_DIR/." "$ISO_DIR/config/includes.chroot/"
install -d -m 0755 "$ISO_DIR/config/includes.chroot/opt/nexus-os"
cp -a "$PROJECT_ROOT/nexus-os/." "$ISO_DIR/config/includes.chroot/opt/nexus-os/"
rm -f -- \
    "$ISO_DIR/config/includes.chroot/opt/nexus-os/kali-tools.html" \
    "$ISO_DIR/config/includes.chroot/opt/nexus-os/kali-tools-data.js"
chmod 0755 \
    "$ISO_DIR/config/includes.chroot/opt/nexus-os/nexus_launch.py" \
    "$ISO_DIR/config/includes.chroot/opt/nexus-os/cleanup-docker.sh" \
    "$ISO_DIR/config/includes.chroot/opt/nexus-os/sanity-test.sh" \
    "$ISO_DIR/config/includes.chroot/usr/local/bin/nexus-openjarvis-chat"
chmod 0755 \
    "$ISO_DIR/config/includes.chroot/usr/local/bin/nexu-configure" \
    "$ISO_DIR/config/includes.chroot/usr/local/bin/nexu-import-data" \
    "$ISO_DIR/config/includes.chroot/usr/local/bin/nexu-avatar"
install -D -m 0644 "$PROJECT_ROOT/nexus-os/ai/personality.json" \
    "$ISO_DIR/config/includes.chroot/etc/nexus-os/personality.json"
rm -f "$ISO_DIR/config/includes.chroot/etc/nexus-os/build-profile.json"
if [ -f "$PROFILE_FILE" ]; then
    python3 "$BUILDER_DIR/apply-profile.py" "$PROFILE_FILE" \
        "$ISO_DIR/config/includes.chroot/etc/nexus-os"
fi
install -D -m 0755 "$BUILDER_DIR/overlay/usr/local/bin/nexu-status.sh" \
    "$ISO_DIR/config/includes.chroot/usr/local/bin/nexu-status.sh"
install -D -m 0644 "$PROJECT_ROOT/nexus-os/ui/dragon-mage.svg" \
    "$ISO_DIR/config/includes.chroot/usr/share/icons/hicolor/scalable/apps/nexus-dragon-mage.svg"
cp "$BUILDER_DIR/hooks/0500-nexus-services.hook.chroot" "$ISO_DIR/config/hooks/live/"
chmod 0755 "$ISO_DIR/config/hooks/live/0500-nexus-services.hook.chroot"

NEXU_BUILD_WRAPPED=1
export NEXU_BUILD_WRAPPED
sh "$ISO_DIR/build.sh"

filesystem=$(find "$ISO_DIR/binary" -type f -name '*.squashfs' -print -quit)
if [ -z "$filesystem" ]; then
    echo "The live-build output contains no SquashFS root filesystem." >&2
    exit 1
fi
metadata=$(unsquashfs -s "$filesystem")
printf '%s\n' "$metadata"
printf '%s\n' "$metadata" | grep -qi 'Compression.*zstd' || {
    echo "RootFS does not use zstd compression." >&2
    exit 1
}
printf '%s\n' "$metadata" | grep -Eq 'Block size[[:space:]]+1048576' || {
    echo "RootFS block size is not 1 MiB." >&2
    exit 1
}

echo "Verified SquashFS format and block size; mksquashfs was invoked with zstd level 19."
