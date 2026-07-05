"""Pack the Debian rootfs into a squashfs and emit a hybrid ISO."""
from __future__ import annotations
import glob as glob_mod
import shutil
import subprocess
from pathlib import Path

from muluos import config

# Debian's live-boot uses ``boot=live`` (not dracut's ``root=live:``).
# ``components`` tells live-boot to look for a squashfs filesystem image.
GRUB_CFG_TEMPLATE = """\
set timeout=5
set default=0

menuentry "MuluOS {version} ({profile}) - Live" {{
    linux /boot/vmlinuz boot=live components quiet splash muluos.mode=live
    initrd /boot/initrd.img
}}
menuentry "MuluOS {version} ({profile}) - Install" {{
    linux /boot/vmlinuz boot=live components quiet splash muluos.mode=live muluos.installer=auto
    initrd /boot/initrd.img
}}
"""

# GRUB core image modules — keep this list minimal so the core image stays small.
BIOS_MODULES = "biosdisk iso9660"
EFI_MODULES = (
    "part_gpt part_msdos fat iso9660 ext2 "
    "normal linux boot configfile search search_label search_fs_uuid "
    "all_video efi_gop efi_uga gfxterm gfxmenu "
    "test loadenv"
)

GRUB_LIB = Path("/usr/lib/grub")


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
    _prepare_boot_images(iso_dir)

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
    """Discover and copy the Debian kernel + initramfs into the ISO staging tree.

    Debian uses versioned filenames (``vmlinuz-6.1.0-XX-amd64``,
    ``initrd.img-6.1.0-XX-amd64``).  We glob for them and copy the first
    match under the fixed names ``vmlinuz`` / ``initrd.img`` so the GRUB
    template doesn't need to know the exact kernel version.
    """
    src_boot = rootfs_dir / "boot"
    vmlinuz_candidates = sorted(src_boot.glob("vmlinuz-*"))
    initrd_candidates = sorted(src_boot.glob("initrd.img-*"))

    if not vmlinuz_candidates:
        raise FileNotFoundError(f"No vmlinuz-* found in {src_boot}")
    if not initrd_candidates:
        raise FileNotFoundError(f"No initrd.img-* found in {src_boot}")

    shutil.copy2(vmlinuz_candidates[0], boot_dir / "vmlinuz")
    shutil.copy2(initrd_candidates[0], boot_dir / "initrd.img")


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


def _prepare_boot_images(iso_dir: Path) -> None:
    """Generate GRUB El Torito (BIOS) and EFI boot images.

    Copies platform modules from the host's /usr/lib/grub into the
    ISO staging tree and builds:
      * boot/grub/i386-pc/eltorito.img  – BIOS El Torito boot catalogue
      * EFI/efiboot.img                 – FAT image wrapping bootx64.efi
    """
    if not GRUB_LIB.is_dir():
        raise FileNotFoundError(
            f"{GRUB_LIB} missing – install grub (apt install grub-pc-bin grub-efi-amd64-bin)"
        )

    # ── BIOS / i386-pc ──────────────────────────────────────────────
    _copy_grub_modules("i386-pc", iso_dir / "boot" / "grub" / "i386-pc")
    eltorito = iso_dir / "boot" / "grub" / "i386-pc" / "eltorito.img"
    subprocess.check_call([
        "grub-mkimage",
        "-O", "i386-pc-eltorito",
        "-o", str(eltorito),
        "-p", "/boot/grub",
        *BIOS_MODULES.split(),
    ])
    eltorito.chmod(0o644)

    # ── EFI / x86_64-efi ────────────────────────────────────────────
    _copy_grub_modules("x86_64-efi", iso_dir / "boot" / "grub" / "x86_64-efi")
    efi_dir = iso_dir / "EFI" / "BOOT"
    efi_dir.mkdir(parents=True, exist_ok=True)
    bootx64 = efi_dir / "bootx64.efi"
    subprocess.check_call([
        "grub-mkimage",
        "-O", "x86_64-efi",
        "-o", str(bootx64),
        "-p", "/boot/grub",
        *EFI_MODULES.split(),
    ])
    bootx64.chmod(0o644)

    # Wrap bootx64.efi inside a FAT filesystem image for the
    # isohybrid El Torito alternate boot entry.
    _make_fat_image(
        iso_dir / "EFI" / "efiboot.img",
        files=[(bootx64, "EFI/BOOT/bootx64.efi")],
        size_mib=10,
    )

    # Clean up the loose bootx64.efi — it lives inside efiboot.img now.
    bootx64.unlink()
    try:
        efi_dir.rmdir()  # only succeeds if empty
    except OSError:
        pass


def _copy_grub_modules(platform: str, dst: Path) -> None:
    """Copy GRUB platform modules from the host into *dst*."""
    src = GRUB_LIB / platform
    if not src.is_dir():
        raise FileNotFoundError(f"GRUB platform missing: {src}")
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _make_fat_image(img_path: Path, *,
                    files: list[tuple[Path, str]],
                    size_mib: int = 10) -> None:
    """Create a FAT image at *img_path* and copy *files* into it.

    Each entry in *files* is (local_path, target_path_inside_image).
    The image is sized to *size_mib* MiB (rounded up to sector boundary).
    """
    # Create and format the image.
    subprocess.check_call([
        "dd", "if=/dev/zero", f"of={img_path}",
        f"bs={size_mib}M", "count=1",
    ])
    subprocess.check_call(["mkfs.vfat", "-F", "32", str(img_path)])

    for local_path, target_path in files:
        # Ensure parent directories exist inside the image.
        parent = Path(target_path).parent
        parts = parent.parts
        for depth in range(1, len(parts) + 1):
            subprocess.check_call(
                ["mmd", "-i", str(img_path), "::" + "/".join(parts[:depth])],
            )
        subprocess.check_call([
            "mcopy", "-i", str(img_path),
            str(local_path), f"::{target_path}",
        ])


def _label_for(profile) -> str:
    return f"MULUOS_{profile.NAME.upper()}"
