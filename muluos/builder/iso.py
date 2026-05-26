"""Pack the rootfs into a squashfs and emit a hybrid ISO."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

from muluos import config

GRUB_CFG_TEMPLATE = """\
set timeout=5
set default=0

menuentry "MuluOS {version} ({profile}) - Live" {{
    linux /boot/vmlinuz-lts root=live:LABEL={label} rd.live.image muluos.mode=live quiet
    initrd /boot/initramfs-lts
}}
menuentry "MuluOS {version} ({profile}) - Install" {{
    linux /boot/vmlinuz-lts root=live:LABEL={label} rd.live.image muluos.mode=live muluos.installer=auto
    initrd /boot/initramfs-lts
}}
"""


def assemble(rootfs_dir: Path, iso_dir: Path, output_dir: Path,
             *, profile, arch: str) -> Path:
    iso_dir.mkdir(parents=True, exist_ok=True)
    boot_dir = iso_dir / "boot"
    grub_dir = boot_dir / "grub"
    live_dir = iso_dir / "live"
    boot_dir.mkdir(parents=True, exist_ok=True)
    grub_dir.mkdir(parents=True, exist_ok=True)
    live_dir.mkdir(parents=True, exist_ok=True)

    _copy_kernel(rootfs_dir, boot_dir)
    _write_grub_cfg(grub_dir, profile=profile)
    _pack_squashfs(rootfs_dir, live_dir / "rootfs.squashfs")

    output_dir.mkdir(parents=True, exist_ok=True)
    iso_path = output_dir / f"muluos-{config.VERSION}-{profile.NAME}-{arch}.iso"
    label = _label_for(profile)
    subprocess.check_call([
        "xorriso", "-as", "mkisofs",
        "-iso-level", "3",
        "-full-iso9660-filenames",
        "-volid", label,
        "-eltorito-boot", "boot/grub/i386-pc/eltorito.img",
        "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table",
        "--grub2-boot-info",
        "-eltorito-alt-boot",
        "-e", "EFI/efiboot.img", "-no-emul-boot",
        "-isohybrid-gpt-basdat",
        "-o", str(iso_path),
        str(iso_dir),
    ])
    return iso_path


def _copy_kernel(rootfs_dir: Path, boot_dir: Path) -> None:
    src_boot = rootfs_dir / "boot"
    for name in ("vmlinuz-lts", "initramfs-lts"):
        src = src_boot / name
        if not src.exists():
            raise FileNotFoundError(f"missing {src}: did mkinitfs run?")
        shutil.copy2(src, boot_dir / name)


def _write_grub_cfg(grub_dir: Path, *, profile) -> None:
    (grub_dir / "grub.cfg").write_text(GRUB_CFG_TEMPLATE.format(
        version=config.VERSION,
        profile=profile.NAME,
        label=_label_for(profile),
    ))


def _pack_squashfs(rootfs_dir: Path, dst: Path) -> None:
    subprocess.check_call([
        "mksquashfs", str(rootfs_dir), str(dst),
        "-comp", "zstd", "-Xcompression-level", "19", "-noappend",
    ])


def _label_for(profile) -> str:
    return f"MULUOS_{profile.NAME.upper()}"
