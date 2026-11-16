#!/bin/sh
# Repack the verified Debian 13.7 amd64 netinst into a Nexus OS installer.
# This path does not require debootstrap/chroot and works from Debian WSL1.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
BASE_ISO=${BASE_ISO:-$SCRIPT_DIR/base/debian-13.7.0-amd64-netinst.iso}
OUTPUT_ISO=${OUTPUT_ISO:-$SCRIPT_DIR/NexusDesktopOS-Security-2026.10-amd64-netinst.iso}
EXPECTED_SHA512=ef04d0276850d70e4aaec0b55003628660e9631b26e35215a70ab3c8c707294a4b12731bc73c75a932902f703a7c278310ca99df28d6b36fb06d5618d8d0f678

for command in xorriso sha512sum cut perl cp mv rm mkdir mktemp grep chmod install node npm; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Missing required command: $command" >&2
        exit 1
    fi
done

if [ ! -f "$BASE_ISO" ]; then
    echo "Base installer ISO not found: $BASE_ISO" >&2
    exit 1
fi

actual_sha512=$(sha512sum "$BASE_ISO" | cut -d ' ' -f 1)
if [ "$actual_sha512" != "$EXPECTED_SHA512" ]; then
    echo "Base ISO SHA-512 does not match the approved Debian 13.7 image." >&2
    exit 1
fi

INCLUDES="$SCRIPT_DIR/config/includes.chroot"
for required in \
    "$INCLUDES/usr/share/nexus-os/index.html" \
    "$PROJECT_ROOT/nexus-os/security-center.html" \
    "$PROJECT_ROOT/nexus-os/nexus-desktopos-wallpaper.svg" \
    "$INCLUDES/etc/systemd/system/nexus-godseye.service" \
    "$INCLUDES/usr/local/bin/nexus-openjarvis-install"; do
    if [ ! -f "$required" ]; then
        echo "Missing Nexus payload file: $required" >&2
        exit 1
    fi
done

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT HUP INT TERM
if ! node --version >/dev/null 2>&1 && [ -x /lib64/ld-linux-x86-64.so.2 ]; then
    # Debian's Node launcher can need the ELF loader explicitly under WSL1.
    mkdir -p "$workdir/bin"
    printf '%s\n' '#!/bin/sh' \
        'exec /lib64/ld-linux-x86-64.so.2 /usr/bin/node "$@"' \
        > "$workdir/bin/node"
    chmod 0755 "$workdir/bin/node"
    PATH="$workdir/bin:$PATH"
    export PATH
fi
mkdir -p "$workdir/nexus-root"
cp -a "$INCLUDES/." "$workdir/nexus-root/"
godseye_root="$workdir/nexus-root/usr/share/nexus-os/godseye"
mkdir -p "$godseye_root/server" "$godseye_root/dist" \
    "$workdir/nexus-root/usr/share/nexus-os" \
    "$workdir/nexus-root/usr/share/doc/nexus-os" \
    "$workdir/nexus-root/usr/local/bin"
# Older build attempts placed Godseye's static files beside server/ rather
# than in the dist/ directory required by its service working directory.
if [ ! -f "$godseye_root/dist/index.html" ]; then
    for item in "$godseye_root"/* "$godseye_root"/.[!.]*; do
        [ -e "$item" ] || continue
        case "${item##*/}" in
            server|dist) continue ;;
        esac
        mv "$item" "$godseye_root/dist/"
    done
fi
# The live-only launcher is not valid in the installed system.
rm -f "$workdir/nexus-root/usr/share/applications/nexus-installer.desktop"

# Refresh app sources directly from the pinned upstream submodules so this
# installer does not depend on a prior live-build run to populate includes.
if [ ! -f "$PROJECT_ROOT/third_party/godseye/dist/index.html" ]; then
    (cd "$PROJECT_ROOT/third_party/godseye" && npm ci && ./node_modules/.bin/vite build --base=./)
fi
cp "$PROJECT_ROOT/nexus-os/security-center.html" \
    "$workdir/nexus-root/usr/share/nexus-os/index.html"
install -D -m 0644 "$PROJECT_ROOT/nexus-os/nexus-desktopos-wallpaper.svg" \
    "$workdir/nexus-root/usr/share/backgrounds/nexus-desktopos.svg"
cp "$PROJECT_ROOT/sat_bench.py" \
    "$workdir/nexus-root/usr/share/nexus-os/sat_bench.py"
cp "$PROJECT_ROOT/third_party/OpenJarvis/README.md" \
    "$workdir/nexus-root/usr/share/nexus-os/OpenJarvis-README.md"
cp "$PROJECT_ROOT/third_party/OpenJarvis/LICENSE" \
    "$workdir/nexus-root/usr/share/doc/nexus-os/OpenJarvis-LICENSE"
cp "$PROJECT_ROOT/third_party/godseye/LICENSE" \
    "$workdir/nexus-root/usr/share/doc/nexus-os/Godseye-LICENSE"
cp "$PROJECT_ROOT/scripts/install-openjarvis.sh" \
    "$workdir/nexus-root/usr/local/bin/nexus-openjarvis-install"
cp -a "$PROJECT_ROOT/third_party/godseye/server/." "$godseye_root/server/"
cp -a "$PROJECT_ROOT/third_party/godseye/dist/." "$godseye_root/dist/"
perl -0pi -e 's/const PORT = Number\(process\.env\.PORT\) \|\| 3001;\R/const PORT = Number(process.env.PORT) || 3001;\nconst HOST = process.env.HOST || '\''127.0.0.1'\'';\n/' \
    "$godseye_root/server/index.mjs"
perl -0pi -e 's/server\.listen\(PORT,\s*\(\) => \{/server.listen(PORT, HOST, () => {/' \
    "$godseye_root/server/index.mjs"
if ! grep -q 'server.listen(PORT, HOST' "$godseye_root/server/index.mjs"; then
    echo "Could not configure Godseye to bind to loopback." >&2
    exit 1
fi

xorriso -osirrox on -indev "$BASE_ISO" \
    -extract /isolinux "$workdir/isolinux" \
    -extract /boot/grub/grub.cfg "$workdir/grub.cfg" \
    -end

set --
for isolinux_config in "$workdir"/isolinux/*.cfg; do
    perl -pi -e 's/(append\s+[^\n]*?)(\s+---)/$1 preseed\/file=\/cdrom\/preseed.cfg$2/' \
        "$isolinux_config"
    set -- "$@" -map "$isolinux_config" "/isolinux/${isolinux_config##*/}"
done
perl -pi -e 's/^(\s*linux\s+[^\n]*?)(\s+---)/$1 preseed\/file=\/cdrom\/preseed.cfg$2/' \
    "$workdir/grub.cfg"

rm -f "$OUTPUT_ISO"
xorriso -indev "$BASE_ISO" -outdev "$OUTPUT_ISO" \
    -volid NEXUS_DESKTOPOS_SEC \
    -map "$SCRIPT_DIR/config/preseed.cfg" /preseed.cfg \
    -map "$workdir/nexus-root" /nexus-root \
    -map "$workdir/grub.cfg" /boot/grub/grub.cfg \
    "$@" \
    -boot_image any replay -commit -end

(cd "$(dirname -- "$OUTPUT_ISO")" && sha512sum "$(basename -- "$OUTPUT_ISO")" \
    > "$(basename -- "$OUTPUT_ISO").sha512")
printf 'ISO: %s\nSHA-512: %s\n' "$OUTPUT_ISO" "$OUTPUT_ISO.sha512"
