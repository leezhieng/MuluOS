"""Install the registry daemon overlay into a rootfs."""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos import config

REGISTRY_OVERLAY = config.ASSETS_DIR / "registry"
EXECUTABLE_PATHS = (
    "usr/libexec/muluos/registryd",
    "usr/libexec/muluos/menu-sync",
    "usr/bin/muluos-reg",
    "usr/bin/muluos-bundle",
    "etc/init.d/muluos-registryd",
    "etc/init.d/muluos-menu-sync",
)


def install(rootfs_dir: Path) -> None:
    if not REGISTRY_OVERLAY.is_dir():
        return
    shutil.copytree(REGISTRY_OVERLAY, rootfs_dir, dirs_exist_ok=True)
    for rel in EXECUTABLE_PATHS:
        target = rootfs_dir / rel
        if target.is_file():
            target.chmod(0o755)
