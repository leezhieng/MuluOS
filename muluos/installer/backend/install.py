"""Copy the live rootfs onto the target disk and apply user config."""
from __future__ import annotations
import subprocess
from pathlib import Path

from . import partition

TARGET = Path("/mnt/muluos")
LIVE_ROOTFS = Path("/run/rootfs")


def copy_rootfs(disk: str, cfg: dict) -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["mount", partition.root_part(disk), str(TARGET)])
    efi_mnt = TARGET / "boot" / "efi"
    efi_mnt.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["mount", partition.efi_part(disk), str(efi_mnt)])

    subprocess.check_call([
        "rsync", "-aHAX",
        "--exclude=/proc/*", "--exclude=/sys/*",
        "--exclude=/dev/*", "--exclude=/run/*",
        "--exclude=/tmp/*", "--exclude=/mnt/*",
        f"{LIVE_ROOTFS}/", f"{TARGET}/",
    ])

    _prune_live_packages()
    _enable_profile_services()
    _write_hostname(cfg["hostname"])
    _write_timezone(cfg["timezone"])
    _create_user(cfg["username"], cfg["password"])


def _prune_live_packages() -> None:
    # Remove live-only X + PyQt6 + agetty from the target. No-op on KDE since
    # plasma re-installs the same packages. Best-effort: apk lacks an
    # autoremove, so transitive orphans may remain.
    profile_marker = TARGET / "etc" / "muluos-profile"
    if not profile_marker.exists() or profile_marker.read_text().strip() == "kde":
        return
    packages_file = TARGET / "etc" / "muluos-live-packages"
    if not packages_file.exists():
        return
    packages = packages_file.read_text().split()
    if not packages:
        return
    subprocess.run(
        ["chroot", str(TARGET), "apk", "del", *packages],
        check=False,
    )
    packages_file.unlink()


def _enable_profile_services() -> None:
    marker = TARGET / "etc" / "muluos-profile"
    if not marker.exists():
        return
    profile = marker.read_text().strip()
    if profile == "kde":
        for svc in ("dbus", "sddm", "muluos-menu-sync"):
            subprocess.check_call([
                "chroot", str(TARGET), "rc-update", "add", svc, "default",
            ])


def _write_hostname(hostname: str) -> None:
    (TARGET / "etc" / "hostname").write_text(hostname + "\n")


def _write_timezone(tz: str) -> None:
    subprocess.check_call([
        "chroot", str(TARGET), "ln", "-sf", f"/usr/share/zoneinfo/{tz}", "/etc/localtime",
    ])


def _create_user(username: str, password: str) -> None:
    subprocess.check_call([
        "chroot", str(TARGET),
        "adduser", "-D", "-G", "wheel", "-s", "/bin/sh", username,
    ])
    subprocess.run(
        ["chroot", str(TARGET), "chpasswd"],
        input=f"{username}:{password}\n".encode(),
        check=True,
    )
