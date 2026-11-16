# NexusDesktopOS Security Edition · amd64

The generated installer is `NexusDesktopOS-Security-2026.10-amd64-netinst.iso`. The next live desktop is a defensive-focused Debian Trixie XFCE image with protection, detection, response, recovery, privacy, and development guidance. It preserves the Nexus workspace, Godseye, Saturn, and optional local OpenJarvis chat setup. Attack, credential-cracking, and wireless-intrusion packages and the separate Kali catalog are excluded. The earlier `NexusOS-13.7.0-amd64.iso` remains available as a separate release.

Defensive packages are selected from Debian repositories; no Kali repository is added. The image does not include exploit, credential-attack, or wireless-attack packages. Tor is not used for system-wide routing by default, and Suricata is not enabled automatically.

## Build the full live desktop

On an amd64 Debian host, install `live-build`, `debian-archive-keyring`, `squashfs-tools`, `syslinux-common`, `xorriso`, `perl`, `git`, `nodejs`, and `npm`, initialize submodules, and ensure at least 20 GB of free space. From the project root, run:

```sh
sudo sh ./nexu-builder/build-iso.sh
```

The version in `VERSION` is `2026.11`. The script creates `NexusDesktopOS-Security-2026.11-amd64.hybrid.iso`, its SHA-256 sidecar, and a `NexusDesktopOS-Security-2026.11-BUILD.txt` build record. It requires root privileges and network access to Debian mirrors. Native Linux is recommended; chroot package setup can fail under WSL.

## Build a smaller network installer

Keep the official Debian 13.7 amd64 netinst image at `iso/base/debian-13.7.0-amd64-netinst.iso`. Its SHA-512 must be:

```text
ef04d0276850d70e4aaec0b55003628660e9631b26e35215a70ab3c8c707294a4b12731bc73c75a932902f703a7c278310ca99df28d6b36fb06d5618d8d0f678
```

Initialize the project submodules, then run:

```sh
cd iso
sh ./build-netinst.sh
```

This installer variant downloads XFCE and the selected Debian defensive packages during installation. The installer was generated as a hybrid BIOS/UEFI ISO and its SHA-512 sidecar was checked. Disk selection remains interactive; no disk is selected or erased automatically.

## Install on a PC

The 2026.11 live ISO boots in legacy BIOS/MBR mode; it does not include a UEFI boot entry. The separate netinst variant has BIOS and UEFI entries. Write the selected ISO to a USB drive with Rufus or balenaEtcher, and review disk and partition choices carefully before confirming installation.

The output uses Debian Trixie repositories, whose package versions can change. Builds are not bit-for-bit reproducible unless repository snapshots and package versions are pinned.
