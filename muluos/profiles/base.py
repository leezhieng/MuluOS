"""Packages shared by every MuluOS profile (Debian)."""
PACKAGES = [
    # Kernel
    "linux-image-amd64",
    # Init system
    "systemd-sysv", "dbus",
    # Package management
    "apt", "apt-utils",
    # Filesystem tools
    "e2fsprogs", "dosfstools", "btrfs-progs",
    # Partitioning
    "parted", "gdisk",
    # Bootloader
    "grub-pc-bin", "grub-efi-amd64-bin", "efibootmgr",
    # Base system
    "python3", "python3-pip",
    "network-manager",
    "openssh-server",
    "sudo",
    "nano",
    "tzdata",
    "rsync",
    "util-linux",
    # Live boot support
    "live-boot", "live-boot-initramfs-tools",
    "squashfs-tools",
    # Initramfs
    "initramfs-tools",
]
