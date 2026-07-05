"""Bootstrap a Debian rootfs via debootstrap + apt-get."""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

from muluos import config
from muluos.builder import bundle, live, registry, settings, utils
from muluos.profiles import base

_REQUIRED_TOOLS = ("debootstrap", "chroot", "mksquashfs", "xorriso")

# Debian places debootstrap and chroot in /usr/sbin, which may not be on a
# regular user's PATH (unlike root's).  Prepend sbin dirs to the search path
# so the check matches what subprocess will find when they are there.
_SBIN_PATH = os.environ.get("PATH", "") + ":/usr/sbin:/sbin:/usr/local/sbin"


def _which(tool: str) -> str | None:
    """Like shutil.which but also searches /usr/sbin and /sbin."""
    return shutil.which(tool, path=_SBIN_PATH)


def _check_tools() -> None:
    """Verify required host tools are available before the build starts."""
    missing = [t for t in _REQUIRED_TOOLS if _which(t) is None]
    if missing:
        raise SystemExit(
            "Missing required build tools: " + ", ".join(missing) + "\n"
            "Install them with:\n"
            "  sudo apt install -y git python3 python3-pip build-essential \\\n"
            "      squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin \\\n"
            "      mtools dosfstools rsync debootstrap\n"
            "\nSee docs/building-and-testing.md §4 for the full list."
        )


def build(rootfs_dir: Path, *, profile, arch: str) -> None:
    """Bootstrap a Debian rootfs in two stages:

    1. ``debootstrap --variant=minbase`` lays down the absolute minimum
       Debian base (no kernel, no init, no apt — just dpkg + essential).
    2. ``chroot apt-get install`` pulls in the full MuluOS package set
       (base + profile + live) on top of that skeleton.

    After packages are installed, overlays are copied in and the chroot
    hook is run — just like the old Alpine path.
    """
    _check_tools()
    rootfs_dir.mkdir(parents=True, exist_ok=True)
    packages = list(base.PACKAGES) + list(profile.PACKAGES) + list(live.PACKAGES)

    # -- Stage 1: debootstrap ------------------------------------------------
    subprocess.check_call([
        "debootstrap",
        "--arch", "amd64",
        "--variant=minbase",
        "--include=ca-certificates",
        config.DEBIAN_CODENAME,
        str(rootfs_dir),
        config.DEBIAN_MIRROR,
    ])

    # -- Stage 2: apt-get install the full package set -----------------------
    _write_apt_sources(rootfs_dir)
    _chroot_apt_install(rootfs_dir, packages)

    # -- Post-install (same overlay + hook pattern as before) -----------------
    _write_live_marker(rootfs_dir)
    _install_installer(rootfs_dir)
    registry.install(rootfs_dir)
    bundle.install(rootfs_dir)
    settings.install(rootfs_dir)
    utils.install(rootfs_dir)
    _run_chroot_hook(rootfs_dir, profile=profile)


def _write_apt_sources(rootfs_dir: Path) -> None:
    """Write /etc/apt/sources.list so apt-get can find packages."""
    sl = rootfs_dir / "etc" / "apt" / "sources.list"
    sl.parent.mkdir(parents=True, exist_ok=True)
    sl.write_text(
        f"deb {config.DEBIAN_MIRROR} {config.DEBIAN_CODENAME} {config.DEBIAN_COMPONENTS}\n"
        f"deb {config.DEBIAN_MIRROR} {config.DEBIAN_CODENAME}-updates {config.DEBIAN_COMPONENTS}\n"
        f"deb {config.DEBIAN_SECURITY} {config.DEBIAN_CODENAME}-security {config.DEBIAN_COMPONENTS}\n"
    )


def _chroot_apt_install(rootfs_dir: Path, packages: list[str]) -> None:
    """Run apt-get update && apt-get install inside the chroot."""
    env = {
        **os.environ,
        "DEBIAN_FRONTEND": "noninteractive",
        "DEBCONF_NONINTERACTIVE_SEEN": "true",
        "LC_ALL": "C",
        "LANGUAGE": "C",
        "LANG": "C",
    }
    subprocess.check_call(
        ["chroot", str(rootfs_dir), "apt-get", "update"],
        env=env,
    )
    subprocess.check_call(
        ["chroot", str(rootfs_dir), "apt-get", "install", "-y",
         "--no-install-recommends", *packages],
        env=env,
    )
    # Shrink the image by cleaning the apt cache.
    subprocess.check_call(
        ["chroot", str(rootfs_dir), "apt-get", "clean"],
        env=env,
    )


def _write_live_marker(rootfs_dir: Path) -> None:
    """Installer reads this to know which packages to prune on a CLI install."""
    marker = rootfs_dir / "etc" / "muluos-live-packages"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("\n".join(live.PACKAGES) + "\n")


def _install_installer(rootfs_dir: Path) -> None:
    target = rootfs_dir / "opt" / "installer"
    target.mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        "cp", "-r", str(config.INSTALLER_SRC) + "/.", str(target),
    ])


def _run_chroot_hook(rootfs_dir: Path, *, profile) -> None:
    hook_src = config.SCRIPTS_DIR / "chroot-hook-debian.sh"
    hook_dst = rootfs_dir / "tmp" / "chroot-hook-debian.sh"
    hook_dst.parent.mkdir(parents=True, exist_ok=True)
    hook_dst.write_bytes(hook_src.read_bytes())
    hook_dst.chmod(0o755)
    subprocess.check_call([
        "chroot", str(rootfs_dir), "/tmp/chroot-hook-debian.sh", profile.NAME,
    ])
    hook_dst.unlink()
