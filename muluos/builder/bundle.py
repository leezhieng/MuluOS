"""Install MuluOS .exe bundle support into a rootfs.

Copies the overlay tree at assets/bundle/ over the rootfs and ensures
the launcher + thumbnailer scripts are executable. MIME and desktop
database refreshes happen inside the chroot hook.
"""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos import config


BUNDLE_OVERLAY = config.ASSETS_DIR / "bundle"
EXECUTABLE_PATHS = (
    "usr/libexec/muluos/launch-bundle",
    "usr/libexec/muluos/bundle-thumbnailer",
)


def install(rootfs_dir: Path) -> None:
    if not BUNDLE_OVERLAY.is_dir():
        return

    shutil.copytree(BUNDLE_OVERLAY, rootfs_dir, dirs_exist_ok=True)

    for rel in EXECUTABLE_PATHS:
        target = rootfs_dir / rel
        if target.is_file():
            target.chmod(0o755)
