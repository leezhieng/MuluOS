"""Run the build inside a Debian container."""
from __future__ import annotations
import subprocess
from pathlib import Path

from muluos import config

BUILD_DEPS = (
    "python3 python3-pip build-essential "
    "squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin "
    "mtools dosfstools rsync debootstrap"
)


def run(*, profile, arch: str, output_dir: Path, work_dir: Path, keep_work: bool) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    inner = (
        f"apt-get update && "
        f"apt-get install -y --no-install-recommends {BUILD_DEPS} && "
        f"python3 build.py --profile {profile.NAME} --arch {arch} "
        f"--work /work --output /dist --force-native"
        f"{' --keep-work' if keep_work else ''}"
    )
    cmd = [
        "docker", "run", "--rm", "--privileged",
        "-v", f"{config.REPO_ROOT}:/src",
        "-v", f"{work_dir}:/work",
        "-v", f"{output_dir}:/dist",
        "-w", "/src",
        config.DOCKER_IMAGES[config.Distribution.DEBIAN],
        "sh", "-c", inner,
    ]
    return subprocess.call(cmd)
