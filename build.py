#!/usr/bin/env python3
"""MuluOS build orchestrator."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from muluos import config
from muluos.builder import host
from muluos.profiles import cli as cli_profile, kde as kde_profile

PROFILES = {
    "cli": cli_profile,
    "kde": kde_profile,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="build.py", description="Build a MuluOS ISO.")
    p.add_argument("--profile", choices=PROFILES.keys(), required=True,
                   help="cli = server (no DE), kde = desktop (KDE Plasma)")
    p.add_argument("--arch", default="x86_64", choices=["x86_64"],
                   help="target architecture")
    p.add_argument("--output", type=Path, default=config.DEFAULT_OUTPUT_DIR,
                   help="directory to write the ISO into")
    p.add_argument("--work", type=Path, default=config.DEFAULT_WORK_DIR,
                   help="scratch directory for rootfs / squashfs staging")
    p.add_argument("--force-docker", action="store_true",
                   help="build inside Docker even if the host is Debian")
    p.add_argument("--force-native", action="store_true",
                   help="refuse to fall back to Docker; require Debian host")
    p.add_argument("--keep-work", action="store_true",
                   help="leave the scratch dir on disk after the build")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profile = PROFILES[args.profile]
    runner = host.select_runner(
        force_docker=args.force_docker,
        force_native=args.force_native,
    )
    return runner.run(
        profile=profile,
        arch=args.arch,
        output_dir=args.output,
        work_dir=args.work,
        keep_work=args.keep_work,
    )


if __name__ == "__main__":
    sys.exit(main())
