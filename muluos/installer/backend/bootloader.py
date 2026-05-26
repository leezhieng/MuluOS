"""GRUB install for BIOS + UEFI."""
from __future__ import annotations
import subprocess

from .install import TARGET


def install(disk: str) -> None:
    for mnt in ("dev", "proc", "sys"):
        subprocess.check_call(["mount", "--bind", f"/{mnt}", str(TARGET / mnt)])

    subprocess.check_call([
        "chroot", str(TARGET),
        "grub-install", "--target=x86_64-efi",
        "--efi-directory=/boot/efi", "--bootloader-id=MuluOS",
    ])
    subprocess.check_call([
        "chroot", str(TARGET), "grub-install", "--target=i386-pc", disk,
    ])
    subprocess.check_call([
        "chroot", str(TARGET), "grub-mkconfig", "-o", "/boot/grub/grub.cfg",
    ])
