"""Build-wide constants and paths."""
from __future__ import annotations
from pathlib import Path

NAME = "MuluOS"
VERSION = "0.1.0-alpha"

ALPINE_BRANCH = "v3.21"
ALPINE_MIRROR = "https://dl-cdn.alpinelinux.org/alpine"

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
SCRIPTS_DIR = REPO_ROOT / "scripts"
INSTALLER_SRC = REPO_ROOT / "muluos" / "installer"

DEFAULT_WORK_DIR = REPO_ROOT / "build"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "dist"

DOCKER_IMAGE = "alpine:3.21"
