"""Pick a build runner based on the host environment."""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos.builder import docker, native


def is_alpine_host() -> bool:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return False
    return "ID=alpine" in os_release.read_text()


def has_docker() -> bool:
    return shutil.which("docker") is not None


def select_runner(*, force_docker: bool = False, force_native: bool = False):
    if force_docker and force_native:
        raise SystemExit("--force-docker and --force-native are mutually exclusive")
    if force_native:
        if not is_alpine_host():
            raise SystemExit("--force-native requires an Alpine host")
        return native
    if force_docker:
        if not has_docker():
            raise SystemExit("--force-docker but docker is not on PATH")
        return docker
    if is_alpine_host():
        return native
    if has_docker():
        return docker
    raise SystemExit(
        "No build path available: not on Alpine and docker is missing. "
        "Install Docker, or run on an Alpine host."
    )
