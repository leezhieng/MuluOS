"""Install the kernel and generate the initramfs inside a Debian rootfs."""
from __future__ import annotations
import subprocess
from pathlib import Path


def install(rootfs_dir: Path, *, profile) -> None:
    """Rebuild the initramfs for all installed kernels.

    Debian's ``live-boot`` and ``live-boot-initramfs-tools`` packages
    (pulled in via the base package list) automatically inject the
    squashfs + overlay hooks into the initramfs.  ``update-initramfs -u``
    is all that's needed to bake them in.
    """
    subprocess.check_call([
        "chroot", str(rootfs_dir),
        "update-initramfs", "-u", "-k", "all",
    ])
