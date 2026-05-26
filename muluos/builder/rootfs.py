"""Bootstrap an Alpine rootfs via apk."""
from __future__ import annotations
import subprocess
from pathlib import Path

from muluos import config
from muluos.builder import bundle, live, registry, settings, utils
from muluos.profiles import base


def build(rootfs_dir: Path, *, profile, arch: str) -> None:
    rootfs_dir.mkdir(parents=True, exist_ok=True)
    packages = list(base.PACKAGES) + list(profile.PACKAGES) + list(live.PACKAGES)

    repo_main = f"{config.ALPINE_MIRROR}/{config.ALPINE_BRANCH}/main"
    repo_community = f"{config.ALPINE_MIRROR}/{config.ALPINE_BRANCH}/community"

    subprocess.check_call([
        "apk",
        "--arch", arch,
        "-X", repo_main,
        "-X", repo_community,
        "-U", "--allow-untrusted",
        "--root", str(rootfs_dir),
        "--initdb",
        "add", *packages,
    ])

    _write_apk_repos(rootfs_dir, repo_main, repo_community)
    _write_live_marker(rootfs_dir)
    _install_installer(rootfs_dir)
    registry.install(rootfs_dir)
    bundle.install(rootfs_dir)
    settings.install(rootfs_dir)
    utils.install(rootfs_dir)
    _run_chroot_hook(rootfs_dir, profile=profile)


def _write_apk_repos(rootfs_dir: Path, *repos: str) -> None:
    etc_apk = rootfs_dir / "etc" / "apk"
    etc_apk.mkdir(parents=True, exist_ok=True)
    (etc_apk / "repositories").write_text("\n".join(repos) + "\n")


def _write_live_marker(rootfs_dir: Path) -> None:
    # Installer reads this to know which packages to prune on a CLI install.
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
    hook_src = config.SCRIPTS_DIR / "chroot-hook.sh"
    hook_dst = rootfs_dir / "tmp" / "chroot-hook.sh"
    hook_dst.parent.mkdir(parents=True, exist_ok=True)
    hook_dst.write_bytes(hook_src.read_bytes())
    hook_dst.chmod(0o755)
    subprocess.check_call([
        "chroot", str(rootfs_dir), "/tmp/chroot-hook.sh", profile.NAME,
    ])
    hook_dst.unlink()
