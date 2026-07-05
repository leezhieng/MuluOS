"""Install the kernel and generate the initramfs inside a Debian rootfs."""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

# chroot lives in /usr/sbin on Debian, which may not be on a regular user's PATH.
_SBIN_PATH = os.environ.get("PATH", "") + ":/usr/sbin:/sbin:/usr/local/sbin"
_CHROOT = shutil.which("chroot", path=_SBIN_PATH)
if _CHROOT is None:
    raise SystemExit(
        "Missing required build tool: chroot\n"
        "Install it with:  sudo apt install -y coreutils\n"
        "See docs/building-and-testing.md §4 for the full list."
    )


def install(rootfs_dir: Path, *, profile) -> None:
    """Rebuild the initramfs for all installed kernels.

    Debian's ``live-boot`` and ``live-boot-initramfs-tools`` packages
    (pulled in via the base package list) automatically inject the
    squashfs + overlay hooks into the initramfs.  ``update-initramfs -u``
    is all that's needed to bake them in.
    """
    subprocess.check_call([
        _CHROOT, str(rootfs_dir),
        "update-initramfs", "-u", "-k", "all",
    ])
