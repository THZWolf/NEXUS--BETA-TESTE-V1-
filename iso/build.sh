#!/bin/sh
# Build the Nexus OS Debian amd64 live/install image. Run on Debian Trixie amd64.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$SCRIPT_DIR"

if [ "$(id -u)" -ne 0 ]; then
    echo "This build needs root privileges: sudo sh ./build.sh" >&2
    exit 1
fi

for command in lb debootstrap sha256sum find install chmod dpkg git node npm cp perl; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Missing required command: $command" >&2
        echo "See README.md for Debian live-build dependencies." >&2
        exit 1
    fi
done

if [ "$(dpkg --print-architecture)" != amd64 ]; then
    echo "Build this x86_64 ISO on an amd64 Debian host (native or amd64 container)." >&2
    exit 1
fi

git -C "$PROJECT_ROOT" submodule update --init --recursive

if [ ! -f "$PROJECT_ROOT/nexus-os/security-center.html" ] || \
   [ ! -f "$PROJECT_ROOT/nexus-os/nexus-desktopos-wallpaper.svg" ]; then
    echo "Missing Security Center or desktop wallpaper under $PROJECT_ROOT/nexus-os" >&2
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/third_party/godseye/package.json" ]; then
    echo "Godseye source is unavailable; initialize repository submodules first." >&2
    exit 1
fi

# Windows checkouts may not preserve executable bits; live-build executes auto/config.
chmod +x "$SCRIPT_DIR/auto/config"
chmod +x "$SCRIPT_DIR"/config/hooks/live/*.hook.chroot
install -D -m 0644 "$PROJECT_ROOT/nexus-os/security-center.html" \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/index.html"
install -D -m 0644 "$PROJECT_ROOT/nexus-os/nexus-desktopos-wallpaper.svg" \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/backgrounds/nexus-desktopos.svg"
install -D -m 0644 "$PROJECT_ROOT/sat_bench.py" \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/sat_bench.py"
install -D -m 0644 "$PROJECT_ROOT/third_party/OpenJarvis/README.md" \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/OpenJarvis-README.md"
install -D -m 0644 "$PROJECT_ROOT/third_party/OpenJarvis/LICENSE" \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/doc/nexus-os/OpenJarvis-LICENSE"
install -D -m 0755 "$PROJECT_ROOT/scripts/install-openjarvis.sh" \
    "$SCRIPT_DIR/config/includes.chroot/usr/local/bin/nexus-openjarvis-install"
install -D -m 0644 "$PROJECT_ROOT/third_party/godseye/LICENSE" \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/doc/nexus-os/Godseye-LICENSE"
mkdir -p "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/godseye/server"
cp -a "$PROJECT_ROOT/third_party/godseye/server/." \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/godseye/server/"
godseye_server="$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/godseye/server/index.mjs"
perl -0pi -e 's/const PORT = Number\(process\.env\.PORT\) \|\| 3001;\R/const PORT = Number(process.env.PORT) || 3001;\nconst HOST = process.env.HOST || '\''127.0.0.1'\'';\n/' "$godseye_server"
perl -0pi -e 's/server\.listen\(PORT,\s*\(\) => \{/server.listen(PORT, HOST, () => {/' "$godseye_server"
if ! grep -q 'server.listen(PORT, HOST' "$godseye_server"; then
    echo "Could not configure Godseye to bind to loopback." >&2
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/third_party/godseye/dist/index.html" ]; then
    echo "Building the Godseye local dashboard..."
    (cd "$PROJECT_ROOT/third_party/godseye" && npm ci && ./node_modules/.bin/vite build --base=./)
fi
mkdir -p "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/godseye/dist"
cp -a "$PROJECT_ROOT/third_party/godseye/dist/." \
    "$SCRIPT_DIR/config/includes.chroot/usr/share/nexus-os/godseye/dist/"

echo "Cleaning previous generated state..."
lb clean --purge

syslinux_modules=/usr/lib/syslinux/modules/bios
for module in ldlinux.c32 libcom32.c32 libutil.c32 vesamenu.c32; do
    if [ ! -f "$syslinux_modules/$module" ]; then
        echo "Missing $syslinux_modules/$module; install syslinux-common." >&2
        exit 1
    fi
    install -D -m 0644 "$syslinux_modules/$module" \
        "$SCRIPT_DIR/config/includes.binary/isolinux/$module"
done

echo "Configuring Debian live-build..."
lb config

if [ "${NEXU_BUILD_WRAPPED:-0}" = "1" ]; then
    echo "Preparing the build chroot to create zstd SquashFS images..."
    lb bootstrap
    lb chroot
    install -D -m 0755 "$PROJECT_ROOT/nexu-builder/bin/mksquashfs" \
        "$SCRIPT_DIR/chroot/usr/local/bin/mksquashfs"
fi

echo "Building ISO; network access and at least 20 GB free space are recommended..."
lb build

iso=$(find "$SCRIPT_DIR" -maxdepth 1 -type f \
    \( -name 'live-image-amd64*.iso' -o -name 'binary.hybrid.iso' \) -print -quit)
if [ -z "$iso" ]; then
    echo "Build finished but no ISO was found at $SCRIPT_DIR" >&2
    exit 1
fi
version=$(cat "$SCRIPT_DIR/VERSION")
case "$version" in
    [0-9][0-9][0-9][0-9].[0-9][0-9]) ;;
    *)
        echo "Invalid ISO version in $SCRIPT_DIR/VERSION: $version" >&2
        exit 1
        ;;
esac
release_iso="$SCRIPT_DIR/NexusDesktopOS-Security-${version}-amd64.hybrid.iso"
if [ "$iso" != "$release_iso" ]; then mv "$iso" "$release_iso"; fi
(cd "$SCRIPT_DIR" && sha256sum "$(basename -- "$release_iso")") > "$release_iso.sha256"
build_info="$SCRIPT_DIR/NexusDesktopOS-Security-${version}-BUILD.txt"
{
    printf 'Version: %s\n' "$version"
    printf 'Build time (UTC): %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'Artifact: %s\n' "$(basename -- "$release_iso")"
    printf 'Architecture: amd64\n'
    printf 'SHA-256: '
    sha256sum "$release_iso" | cut -d ' ' -f 1
} > "$build_info"
printf 'ISO: %s\nSHA-256: %s\nBuild info: %s\n' \
    "$release_iso" "$release_iso.sha256" "$build_info"
echo "Build inputs are not snapshot-pinned; this is not a bit-for-bit reproducible release."
