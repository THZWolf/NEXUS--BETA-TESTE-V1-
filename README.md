# Nexus OS Security Edition

Nexus OS 2026.11 is a Debian amd64 live desktop focused on defensive security, privacy, incident response, and recovery. The ISO uses Debian repositories only; it excludes Kali repositories and the separate Kali tool catalog. Sensors are not started or configured automatically.

## Build

Build on an amd64 Debian host with root privileges, network access, and at least 20 GB of free space. Install `live-build`, `debian-archive-keyring`, `squashfs-tools`, `syslinux-common`, `xorriso`, `perl`, `git`, `nodejs`, and `npm`, then clone with submodules and run:

```sh
git clone --recurse-submodules https://github.com/THZWolf/NEXUS--BETA-TESTE-V1-.git
cd NEXUS--BETA-TESTE-V1-
sudo sh ./nexu-builder/build-iso.sh
```

The build produces a BIOS/MBR-bootable hybrid ISO, a SHA-256 sidecar, and a build record in `iso/`. The 2026.11 live image has no UEFI boot entry. SquashFS uses zstd with 1 MiB blocks. Build inputs are not snapshot-pinned, so builds are not bit-for-bit reproducible.

## Included features

- Portuguese-language Security Center for protection, detection, response, recovery, and privacy.
- Defensive monitoring and forensic packages from Debian.
- OpenJarvis is optional; its local `chat-simple` setup is explicit, and model/runtime downloads are separate.
- Local services bind to loopback unless a feature explicitly documents otherwise.

The ISO is a defensive administration environment, not an automated audit or scanning product. Use all tools only on systems you own or are authorized to administer.