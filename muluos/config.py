"""Build-wide constants and paths."""
from __future__ import annotations
from enum import Enum
from pathlib import Path

NAME = "MuluOS"
VERSION = "0.1.0-alpha"

# ── Distribution enum ─────────────────────────────────────────────────────────

class Distribution(Enum):
    """Target Linux distribution for the build."""
    ALPINE = "alpine"
    DEBIAN = "debian"

# Default to Debian.  Swap back to Distribution.ALPINE to restore the old path.
DEFAULT_DISTRO = Distribution.DEBIAN

# ── Alpine constants (kept for backward compatibility) ────────────────────────

ALPINE_BRANCH = "v3.21"
ALPINE_MIRROR = "https://dl-cdn.alpinelinux.org/alpine"

# ── Debian constants ──────────────────────────────────────────────────────────

DEBIAN_CODENAME = "trixie"                  # Debian 13 (testing)
DEBIAN_MIRROR = "http://deb.debian.org/debian"
DEBIAN_COMPONENTS = "main contrib non-free non-free-firmware"
DEBIAN_SECURITY = "http://security.debian.org/debian-security"

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
SCRIPTS_DIR = REPO_ROOT / "scripts"
INSTALLER_SRC = REPO_ROOT / "muluos" / "installer"

DEFAULT_WORK_DIR = REPO_ROOT / "build"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "dist"

# ── Docker images per distribution ────────────────────────────────────────────

DOCKER_IMAGES = {
    Distribution.ALPINE: "alpine:3.21",
    Distribution.DEBIAN: "debian:trixie-slim",
}

# Legacy alias (used before multi-distro support was added).
DOCKER_IMAGE = DOCKER_IMAGES[Distribution.ALPINE]
