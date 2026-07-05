# `scripts/` — host and chroot helpers

This directory holds shell scripts that the build system invokes at
specific moments. Anything that needs to run inside the target rootfs
lives here; per-application overlays live under `assets/` instead.

## `chroot-hook-debian.sh`

The script the builder copies into the freshly-bootstrapped Debian
rootfs and executes via `chroot`. It is *the* place to do anything that
needs to run "inside the target system before the image is sealed":
enabling services, refreshing caches, generating files whose paths
depend on installed package versions.

**Invocation.** Called by `muluos.builder.rootfs._run_chroot_hook()`
with one argument — the profile name (`cli` or `kde`):

```
chroot <rootfs> /tmp/chroot-hook-debian.sh <profile>
```

The script is deleted after it runs.

**What it does, in order:**

1. **systemd service enablement** — `systemctl enable NetworkManager`,
   `systemctl enable ssh`. These run regardless of profile.
2. **Python site-dir bootstrap** — queries the installed `python3` for
   its `purelib` directory and drops a `muluos.pth` file there pointing
   at `/usr/lib/muluos`. This makes `import muluos_registry` work in
   any process without hardcoding a python3.X minor version.
3. **Registry daemon enable** — `systemctl enable muluos-registryd`
   (core to every profile; the daemon binds the socket that the bundle
   launcher needs).
4. **Environment generator enable** — `systemctl enable muluos-env-generate`
   (regenerates `/etc/profile.d/muluos-env.sh` from the registry on boot).
5. **KDE-only services** — if `$PROFILE = kde`, enables `muluos-menu-sync`.
   SDDM and dbus are NOT enabled here — the installer does that post-install
   so the live ISO can launch the PyQt6 installer via `startx` instead.
6. **sudo for live media** — drops a `%sudo` NOPASSWD entry in
   `/etc/sudoers.d/`. Intended for the live-install media; the
   installer should tighten this on the real installed system.
7. **Live-mode TTY auto-login** — creates a systemd drop-in at
   `getty@tty1.service.d/autologin.conf` that auto-logs root on tty1.
8. **Live-mode X auto-launch** — writes `/root/.bash_profile` and
   `/root/.xinitrc` so that `startx` + the PyQt6 installer fire
   automatically when booting with `muluos.mode=live` on the kernel
   command line.
9. **Bundle launcher / thumbnailer chmod** — defensive chmod 0755 on
   the `.exe` bundle support scripts in case `shutil.copytree` lost the
   mode bits.
10. **MIME and desktop database refresh** — runs `update-mime-database`
    and `update-desktop-database` (guarded by `command -v`) so the
    `application/x-muluos-bundle` MIME type, the bundle launcher
    `.desktop`, and the Dolphin service menu are all picked up by KDE.

If you need to add a step, put it alongside the existing `systemctl enable`
blocks for service changes, near the `cat > ... <<'EOF'` blocks for file
generation, and near the bottom for cache refreshes.

**What does NOT belong here:**

- Per-application config that ships verbatim — that's an overlay
  (`assets/<name>/`) plus a `muluos.builder.<name>.install()` helper.
- Anything you'd want to re-run on a *running* system — those go in
  CLI tools (`muluos-bundle install`, etc.).
- Anything specific to the build host. Host-side prep lives in
  `muluos/builder/host.py`.

## `chroot-hook.sh`

The original Alpine/OpenRC variant of the chroot hook. Kept for backward
compatibility with Alpine-based builds. Uses `rc-update add` for service
enablement and `/etc/inittab` for TTY auto-login. Not used by the default
(Debian) build path — see `chroot-hook-debian.sh` instead.

## Adding new scripts

If a step is genuinely shell-shaped and runs in the chroot, add it to
`chroot-hook-debian.sh` rather than creating a second script — keeping a
single entry point makes the chroot phase easy to reason about.

If the step needs to be re-runnable on the installed system (e.g.,
periodic maintenance), make it a CLI tool in an overlay (mirroring
`/usr/bin/muluos-reg` and `/usr/bin/muluos-bundle`) and just *enable*
it from the chroot hook.
