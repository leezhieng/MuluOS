"""Install MuluOS utility tools into a rootfs.

Each immediate subdirectory of utils/ is a rootfs overlay for one tool,
laid out by install destination, e.g.:

    utils/<tool>/usr/bin/muluos-<tool>
    utils/<tool>/usr/lib/muluos/<tool>/...
    utils/<tool>/usr/share/applications/muluos-<tool>.desktop

Every tool tree is copied over the rootfs. Files landing under usr/bin,
usr/sbin, or usr/libexec/muluos are marked executable.
"""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos import config

UTILS_DIR = config.REPO_ROOT / "utils"
EXECUTABLE_PARENTS = ("usr/bin", "usr/sbin", "usr/libexec/muluos", "etc/init.d")


def install(rootfs_dir: Path) -> None:
    if not UTILS_DIR.is_dir():
        return
    for tool_dir in sorted(UTILS_DIR.iterdir()):
        if not tool_dir.is_dir():
            continue
        shutil.copytree(tool_dir, rootfs_dir, dirs_exist_ok=True)
        _fix_executables(tool_dir, rootfs_dir)


def _fix_executables(tool_dir: Path, rootfs_dir: Path) -> None:
    for parent in EXECUTABLE_PARENTS:
        src_parent = tool_dir / parent
        if not src_parent.is_dir():
            continue
        for src in src_parent.rglob("*"):
            if src.is_file():
                (rootfs_dir / src.relative_to(tool_dir)).chmod(0o755)
