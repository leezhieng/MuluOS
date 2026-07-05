"""Pick a build runner based on the host environment."""
from __future__ import annotations
import shutil
from pathlib import Path

from muluos import config
from muluos.builder import docker, native


def detect_distro() -> config.Distribution | None:
    """Return the host distribution or None if unrecognized."""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return None
    content = os_release.read_text()
    if "ID=alpine" in content:
        return config.Distribution.ALPINE
    if "ID=debian" in content:
        return config.Distribution.DEBIAN
    # Catch Debian derivatives (Ubuntu, etc.).
    if "ID_LIKE=debian" in content:
        return config.Distribution.DEBIAN
    return None


def has_docker() -> bool:
    return shutil.which("docker") is not None


def select_runner(*, force_docker: bool = False, force_native: bool = False):
    distro = config.DEFAULT_DISTRO

    if force_docker and force_native:
        raise SystemExit("--force-docker and --force-native are mutually exclusive")

    if force_native:
        host = detect_distro()
        if host != distro:
            raise SystemExit(
                f"--force-native requires a {distro.value} host "
                f"(detected {host.value if host else 'unknown'})"
            )
        return native

    if force_docker:
        if not has_docker():
            raise SystemExit("--force-docker but docker is not on PATH")
        return docker

    # Auto-detect: prefer native when the host matches the target distro.
    host = detect_distro()
    if host == distro:
        return native
    if has_docker():
        return docker

    raise SystemExit(
        f"No build path available: not on {distro.value} and docker is missing. "
        "Install Docker, or run on a Debian host."
    )
