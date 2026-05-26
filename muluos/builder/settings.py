"""Install the MuluOS Settings PyQt6 app overlay into a rootfs."""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos import config

SETTINGS_OVERLAY = config.ASSETS_DIR / "settings"
EXECUTABLE_PATHS = (
    "usr/bin/muluos-settings",
)


def install(rootfs_dir: Path) -> None:
    if not SETTINGS_OVERLAY.is_dir():
        return
    shutil.copytree(SETTINGS_OVERLAY, rootfs_dir, dirs_exist_ok=True)
    for rel in EXECUTABLE_PATHS:
        target = rootfs_dir / rel
        if target.is_file():
            target.chmod(0o755)
