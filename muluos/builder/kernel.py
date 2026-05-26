"""Install the kernel and generate the initramfs inside the rootfs."""
from __future__ import annotations
import subprocess
from pathlib import Path

INITFS_FEATURES = "ata base ide scsi usb virtio ext4 squashfs overlay nvme"


def install(rootfs_dir: Path, *, profile) -> None:
    # linux-lts is pulled in via the base package list; rebuild initramfs
    # so it picks up squashfs + overlay for the live boot.
    subprocess.check_call([
        "chroot", str(rootfs_dir),
        "mkinitfs", "-F", INITFS_FEATURES,
    ])
