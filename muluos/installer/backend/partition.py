"""Disk discovery and partitioning via sgdisk."""
from __future__ import annotations
import subprocess


def list_disks() -> list[str]:
    out = subprocess.check_output(["lsblk", "-dno", "NAME,TYPE"], text=True)
    return [
        f"/dev/{parts[0]}"
        for line in out.splitlines()
        if (parts := line.split()) and parts[1] == "disk"
    ]


def partition(disk: str) -> None:
    # GPT layout: 512 MiB EFI, remainder for root.
    subprocess.check_call(["sgdisk", "--zap-all", disk])
    subprocess.check_call([
        "sgdisk",
        "-n", "1:0:+512M", "-t", "1:ef00", "-c", "1:EFI",
        "-n", "2:0:0",    "-t", "2:8300", "-c", "2:MULUOS",
        disk,
    ])
    subprocess.check_call(["partprobe", disk])


def efi_part(disk: str) -> str:
    return _suffix(disk, 1)


def root_part(disk: str) -> str:
    return _suffix(disk, 2)


def _suffix(disk: str, n: int) -> str:
    # NVMe devices use pN; everything else just N.
    return f"{disk}p{n}" if disk[-1].isdigit() else f"{disk}{n}"
