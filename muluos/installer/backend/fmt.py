"""mkfs wrappers. Named fmt to avoid shadowing the stdlib format builtin."""
from __future__ import annotations
import subprocess

from . import partition


def format_partitions(disk: str) -> None:
    subprocess.check_call(["mkfs.vfat", "-F32", partition.efi_part(disk)])
    subprocess.check_call(["mkfs.ext4", "-F", partition.root_part(disk)])
