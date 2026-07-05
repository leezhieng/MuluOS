"""Native Debian build path."""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos.builder import iso, kernel, rootfs


def run(*, profile, arch: str, output_dir: Path, work_dir: Path, keep_work: bool) -> int:
    rootfs_dir = work_dir / "rootfs"
    iso_dir = work_dir / "iso"

    rootfs.build(rootfs_dir, profile=profile, arch=arch)
    kernel.install(rootfs_dir, profile=profile)
    iso_path = iso.assemble(rootfs_dir, iso_dir, output_dir, profile=profile, arch=arch)

    print(f"built {iso_path}")
    if not keep_work:
        shutil.rmtree(work_dir, ignore_errors=True)
    return 0
