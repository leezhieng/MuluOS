"""Run the build inside an Alpine container."""
from __future__ import annotations
import subprocess
from pathlib import Path

from muluos import config

BUILD_DEPS = (
    "python3 py3-pip alpine-sdk apk-tools "
    "squashfs-tools xorriso grub grub-efi mtools dosfstools rsync"
)


def run(*, profile, arch: str, output_dir: Path, work_dir: Path, keep_work: bool) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    inner = (
        f"apk add --no-cache {BUILD_DEPS} && "
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
        config.DOCKER_IMAGE,
        "sh", "-c", inner,
    ]
    return subprocess.call(cmd)
